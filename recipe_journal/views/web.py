"""
Module containing all views for the Django application.

Views included:
    - login: Handles user login and session creation.
    - logout: Logs out the user by removing their session.
    - register: Manages user registration and redirects to login upon success.
    - welcome: Displays the homepage with popular recipes and logged-in user info.
    - add_recipe: Handles the process of adding a new recipe, validating forms and saving data.
    - show_confirmation_page: Displays a confirmation page after recipe addition.
    - show_recipe: Displays a detailed view of a specific recipe.
    - show_friends: Manages adding a friend to the user's friend list.
    - show_recipe_collection: Displays a member's recipe collection (album, to-try, history).
    - search_recipe:
"""

from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from recipe_journal.forms import LoginForm, AddFriendForm, ModifyProfileForm
from recipe_journal.forms import RegistrationForm, SearchRecipeForm
from recipe_journal.models import Member, Recipe, RecipeAlbumEntry, RecipeHistoryEntry, RecipeToTryEntry
import recipe_journal.utils.utils as ut
from recipe_journal.models import Recipe, RecipeHistoryEntry, RecipeAlbumEntry, RecipeToTryEntry

MODEL_MAP = {
        "RecipeAlbumEntry": RecipeAlbumEntry,
        "RecipeToTryEntry": RecipeToTryEntry,
        "RecipeHistoryEntry": RecipeHistoryEntry
    }

def login(request):
    """
    Handles user login by processing the login form and creating a user session.
    """
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            logged_user = Member.objects.get(username=username)
            request.session["logged_user_id"] = logged_user.id
            return redirect("/welcome")
        else:
            return render(request, "login.html", {"form": form})
    else:
        form = LoginForm()
        return render(request, "login.html", {"form": form})
    
def logout(request):
    """
    Logs out the user by removing their session identifier and redirects to the homepage.
    """
    if "logged_user_id" in request.session:
        del request.session["logged_user_id"]
    return redirect("/welcome")

def register(request):
    """
    Manages user registration by processing the registration form and redirecting to the login page upon success.
    """
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/login")
        else:
            return render(request, "register.html", {"form": form})
    else:
        form = RegistrationForm()
        return render(request, "register.html", {"form": form})

def modify_profile(request):
    logged_user = ut.get_logged_user(request)
    if not logged_user:
        return redirect("/login")
    if request.method == "POST" and len(request.POST)>0:
        form = ModifyProfileForm(request.POST, instance=logged_user, logged_user=logged_user)
        if form.is_valid():
            form.save()
            return redirect("/login")
        else:
            return render(request, "modify_profile.html", {"form": form, "logged_user": logged_user})
    else:
        form = ModifyProfileForm(instance=logged_user, logged_user=logged_user)
    return render(request, "modify_profile.html", {"form": form, "logged_user": logged_user})

def welcome(request):
    """
    Displays the homepage with a list of popular recipes, thumbnails, and logged-in user information if available.
    """
    TOP_RECIPE_NB = 2
    THUMBNAIL_RECIPE_NB = 12

    logged_user = ut.get_logged_user(request)
    top_recipe_ids_list = ut.get_daily_random_sample(TOP_RECIPE_NB)
    top_recipe_list = Recipe.objects.filter(id__in=top_recipe_ids_list)
    thumbnail_recipe_ids_list = ut.get_daily_random_sample(THUMBNAIL_RECIPE_NB)
    thumbnail_recipe_list = Recipe.objects.filter(id__in=thumbnail_recipe_ids_list)

    context = {
        "logged_user": logged_user,
        "top_recipe_list": top_recipe_list,
        "thumbnail_recipes": thumbnail_recipe_list,
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, "welcome.html", context)

@require_http_methods(["POST"])
def add_recipe(request):
    """
    Handles adding a new recipe by validating forms, saving the recipe and ingredients, 
    and processing associated actions (collections). Redirects to the confirmation page upon success.
    """
    logged_user = ut.get_logged_user(request)
    if not logged_user:
        return redirect("/login")

    recipe_form, recipe_ingredient_form_list, recipe_action_form = ut.prepare_recipe_forms(request)

    if ut.are_forms_valid(*recipe_ingredient_form_list, recipe_form, recipe_action_form):
        recipe = ut.save_recipe_with_ingredients(recipe_form, recipe_ingredient_form_list)
        ut.handle_recipe_collections(recipe_action_form, logged_user, recipe, request)
        return redirect("/show-confirmation-page")
        
    else:
        context = {
            "logged_user": logged_user,
            "recipe_form": recipe_form,
            "recipe_ingredient_form_list": recipe_ingredient_form_list,
            "recipe_action_form": recipe_action_form
            }
        return render(request, "add_recipe.html", context)

def show_confirmation_page(request):
    """
    Displays the confirmation page after a successful recipe addition.
    """
    logged_user = ut.get_logged_user(request)
    if not logged_user:
        return redirect("/login")

    return render(request, "confirmation_page.html", { "logged_user": logged_user })

def show_recipe(request):
    """
    Displays the requested recipe if the recipe ID is valid, otherwise redirects to the homepage.
    """
    logged_user = ut.get_logged_user(request)

    if request.method == "GET" and "recipe-id" in request.GET:
        recipe_id = request.GET["recipe-id"]
        result = Recipe.objects.filter(id = recipe_id)
        if len(result) == 1:
            recipe = Recipe.objects.get(id = recipe_id)
            context = {
                "logged_user": logged_user,
                "recipe": recipe,
                "MEDIA_URL": settings.MEDIA_URL,
            }
            return render(request, "show_recipe.html", context)
    
    return redirect("/welcome")

def show_friends(request):
    """Displays the logged-in user's friend list and handles adding or removing friends."""
    logged_user = ut.get_logged_user(request)
    if not logged_user:
        return redirect("/login")

    form = AddFriendForm(logged_user=logged_user)

    if request.method == "POST" and "username_to_add" in request.POST:
        form = ut.handle_add_friend_request(request, logged_user)

    elif request.method == "POST" and "username_to_remove" in request.POST:
        ut.handle_remove_friend_request(request, logged_user)

    friends = logged_user.friends.order_by("username")

    context = {
        "logged_user": logged_user,
        "friends": friends,
        "form": form,
    }
    return render(request, "show_friends.html", context)

def show_recipe_collection(request):
    """
    Displays a member's recipe collection for a specified collection model (album, to-try, history).
    """
    logged_user = ut.get_logged_user(request)
    if not logged_user:
        return redirect("/login")
    
    form, recipe_collection_entries = ut.filter_recipe_collection(request)

    if not form:
        return redirect("/welcome")

    form_html = render_to_string("partials/form_filter_recipe_collection.html", {"form": form}, request=request)
    member = getattr(form, "cleaned_data", {}).get("member", None)
    collection_name = getattr(form, "cleaned_data", {}).get("collection", None)
    collection_model = MODEL_MAP.get(collection_name)
    
    context = {
        "logged_user": logged_user,
        "form": form_html,
        "member": member,
        "collection_model": collection_model,
        "recipe_entries": recipe_collection_entries,
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, "show_recipe_collection.html", context)

def search_recipe(request):
    """Handles recipe search and renders the search page."""
    logged_user = ut.get_logged_user(request)
    
    if not logged_user:
        return redirect("/login")
    
    form = SearchRecipeForm()
    recipe_entries = Recipe.objects.all()

    if request.method == "GET":
        form, recipe_entries = ut.handle_search_recipe_request(request, logged_user)
       
    form_html = render_to_string("partials/form_search_recipe.html", {"form": form}, request=request)

    
    context = {
    "logged_user": logged_user,
    "thumbnail_recipes": recipe_entries,
    "form": form_html,
    "MEDIA_URL": settings.MEDIA_URL,
    }

    return render(request, "search_recipe.html", context)


