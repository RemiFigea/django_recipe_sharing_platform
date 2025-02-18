"""
Module managing the main views of the application, which are accessible through regular web pages.
"""
from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from recipe_journal.forms import LoginForm, AddFriendForm, AddRecipeToCollectionsForm, ModifyProfileForm
from recipe_journal.forms import RecipeCombinedForm, RecipeIngredientForm, RegistrationForm, SearchRecipeForm
from recipe_journal.models import Member, Recipe, RecipeCollectionEntry
import recipe_journal.utils.utils as ut

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
    """Handles the modification of the logged user's profile."""

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
    Displays the homepage with a list of randomly selected recipes, thumbnails,
    and logged-in user information if available.
    """
    TOP_RECIPE_NB = 2
    THUMBNAIL_RECIPE_NB = 12

    logged_user = ut.get_logged_user(request)
    recipe_ids_list = ut.get_daily_random_sample(TOP_RECIPE_NB + THUMBNAIL_RECIPE_NB)
    top_recipe_qs, thumbnail_recipe_qs = ut.get_top_and_thumbnail_recipes(recipe_ids_list, TOP_RECIPE_NB)

    context = {
        "logged_user": logged_user,
        "top_recipe_qs": top_recipe_qs,
        "thumbnail_recipe_qs": thumbnail_recipe_qs,
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, "welcome.html", context)

def add_recipe(request):
    """
    Handles adding a new recipe by validating forms, saving the recipe and ingredients, 
    and adding to the logged-in user recipe collections. Redirects to the confirmation page upon success.
    """
    logged_user = ut.get_logged_user(request)
    if not logged_user:
        return redirect("/login")
    
    if request.method != "POST":
        recipe_form = RecipeCombinedForm()
        recipe_ingredient_form_list = [RecipeIngredientForm()]
        add_recipe_to_collection_form = AddRecipeToCollectionsForm()

    if request.method == "POST":
        recipe_form, recipe_ingredient_form_list, add_recipe_to_collection_form = ut.prepare_recipe_forms(request)

        if ut.are_forms_valid(*recipe_ingredient_form_list, recipe_form, add_recipe_to_collection_form):
            recipe = ut.save_recipe_and_ingredients(recipe_form, recipe_ingredient_form_list)
            ut.add_recipe_to_collections(add_recipe_to_collection_form, logged_user, recipe, request)
            return redirect("/show-confirmation-page")
            
    context = {
        "logged_user": logged_user,
        "recipe_form": recipe_form,
        "recipe_ingredient_form_list": recipe_ingredient_form_list,
        "manage_recipe_collection_form": add_recipe_to_collection_form
        }
    return render(request, "add_recipe.html", context)

def show_confirmation_page(request):
    """Displays the confirmation page after a successful recipe addition."""

    logged_user = ut.get_logged_user(request)
    if not logged_user:
        return redirect("/login")

    return render(request, "confirmation_page.html", { "logged_user": logged_user })

@require_http_methods(["GET"])
def show_recipe(request):
    """
    Displays the requested recipe if the recipe ID is valid, otherwise redirects to the homepage.
    """
    logged_user = ut.get_logged_user(request)
    recipe_id = request.GET.get("recipe-id")
    
    if not recipe_id or not recipe_id.isdigit():
        return redirect("/welcome")
    
    recipe = get_object_or_404(Recipe, id=int(recipe_id))
        
    context = {
        "logged_user": logged_user,
        "recipe": recipe,
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, "show_recipe.html", context)

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

def search_recipe(request):
    """
    Handles the recipe search by processing the search form, retrieving matching recipes, 
    and displaying them based on the user's collection selection. Returns the search results page.
    """
    logged_user = ut.get_logged_user(request)

    if request.method == "GET":
        form, recipe_collection_qs, recipe_qs = ut.handle_search_recipe_request(request, logged_user)
    else:
        form = SearchRecipeForm(logged_user=logged_user)
        recipe_collection_qs = RecipeCollectionEntry.objects.none()
        recipe_qs = Recipe.objects.all().order_by("title")
       
    form_html = render_to_string("partials/form_search_recipe.html", {"form": form}, request=request)
    collection_name = getattr(form, "cleaned_data", {}).get("collection_name", None)

    context = {
    "logged_user": logged_user,
    "collection_name": collection_name,
    "recipe_collection_qs": recipe_collection_qs,
    "thumbnail_recipe_qs": recipe_qs,
    "form": form_html,
    "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, "search_recipe.html", context)

def show_recipe_collection(request):
    """
    Displays the recipes in a specific collection based on the selected collection and member.
    Processes the form submission and shows the recipes in the chosen collection.
    """
    logged_user = ut.get_logged_user(request)
    if not logged_user:
        return redirect("/login")
    
    if request.method == "POST":
        form, recipe_collection_qs = ut.handle_show_recipe_collection_request(request)
    else:
        return redirect("/welcome")

    form_html = render_to_string("partials/form_show_recipe_collection.html", {"form": form}, request=request)
    member = getattr(form, "cleaned_data", {}).get("member", None)
    collection_name = getattr(form, "cleaned_data", {}).get("collection_name", None)
    collection_title = dict(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES).get(collection_name)

    context = {
        "logged_user": logged_user,
        "member": member,
        "collection_name": collection_name,
        "collection_title": collection_title,
        "recipe_collection_qs": recipe_collection_qs,
        "form": form_html,
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, "show_recipe_collection.html", context)




