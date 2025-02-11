"""
Module interacting with JavaScript functions to dynamically update the template.

Functions included:
    - check_title: Validates if a recipe title is unique and properly formatted.
    - add_ingredient_form: Dynamically adds an ingredient form and renders it.
    - check_collection_status: Checks if a recipe is already in a user's collection (album, to-try, or history).
    - add_to_collection: Adds a recipe to a user's collection (album, to-try, or history) if it's not already there.
    - remove_from_collection: Removes a recipe from a user's collection (album, to-try, or history).
    - add_recipe_history:
    - remove_recipe_history:
"""
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from recipe_journal.forms import RecipeIngredientForm, CreateRecipeHistoryForm, DeleteRecipeHistoryForm
from recipe_journal.models import Member, Recipe, RecipeHistoryEntry, RecipeAlbumEntry, RecipeToTryEntry
import recipe_journal.utils.utils as ut

MODEL_MAP = {
            "RecipeAlbumEntry": RecipeAlbumEntry,
            "RecipeToTryEntry": RecipeToTryEntry,
            "RecipeHistoryEntry": RecipeHistoryEntry
        }

@require_http_methods(["GET"])
def check_title(request):
    """
    Validates if a recipe title is unique and properly formatted.

    Parameters:
    - request (HttpRequest): The HTTP request object containing the title to check.

    Returns:
    - JsonResponse: A response containing error messages if validation fails, or an empty list if the title is valid.
    """
    if "title" not in request.GET:
        return JsonResponse({"message": "'title' absent de l'objet request."}, status=400)
    
    title = request.GET.get("title")
    error_list = ut.validate_title(title)

    if not error_list and Recipe.objects.filter(title=title).exists():
        error_list = ["Ce titre de recette est déjà utilisé!"]
    
    if error_list:
        return JsonResponse({"error_list": error_list})
    else:
        return JsonResponse({"error_list": []})

@require_http_methods(["GET"])  
def add_ingredient_form(request):
    """
    Dynamically adds an ingredient form and renders it.

    Parameters:
    - request (HttpRequest): The HTTP request object.

    Returns:
    - HttpResponse: The HTML response containing the rendered ingredient form.
    """
    new_form = RecipeIngredientForm()
    form_html = render_to_string("partials/form_recipe_ingredient.html", {"form": new_form}, request=request)
    return JsonResponse({"form_html": form_html})

@require_http_methods(["POST"])
def check_collection_status(request):
    logged_user, recipe_id, model, error_response = ut.check_request_validity(request)
    if error_response:
        return error_response
  
    is_in_collection = model.objects.filter(member=logged_user, recipe_id=recipe_id).exists()

    return JsonResponse({"is_in_collection": is_in_collection})

@require_http_methods(["POST"])
def add_to_collection(request):
    return ut.manage_collection(request, "add")

@require_http_methods(["POST"])
def remove_from_collection(request):
    return ut.manage_collection(request, "remove")

@require_http_methods(["POST"])
def add_recipe_history(request):
    """
    Adds a recipe to a user's history.

    Parameters:
    - request (HttpRequest): The HTTP request containing the recipe data to be saved.

    Returns:
    - JsonResponse: A response indicating success or failure, with form validation errors if applicable.
    """
    form = CreateRecipeHistoryForm(request.POST)

    if form.is_valid():
        form.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "errors": form.errors})
    
@require_http_methods(["POST"])
def remove_recipe_history(request):
    """
    Removes a recipe from a user's history.

    Parameters:
    - request (HttpRequest): The HTTP request containing the member ID, recipe ID, and history entry date.

    Returns:
    - JsonResponse: A response indicating success or failure, with updated form HTML if applicable.
    """
    member = get_object_or_404(Member, id=request.POST.get("member"))
    recipe = get_object_or_404(Recipe, id=request.POST.get("recipe"))

    form = DeleteRecipeHistoryForm(request.POST, member=member, recipe=recipe)

    if form.is_valid():
        recipe_history_entry_date = form.cleaned_data["recipe_history_entry_date"]

        count, _ = RecipeHistoryEntry.objects.filter(
            member=form.member, recipe=form.recipe, saving_date=recipe_history_entry_date
        ).delete()

        form_html = DeleteRecipeHistoryForm(member=member, recipe=recipe).as_p()

        if count > 0:
            return JsonResponse({"success": True, "form_html": form_html})
    
        else:
            return JsonResponse({"success": False, "errors": "Une erreur est survenue.", "form_html": form_html})

    form._errors.clear()
    form_html = form.as_p()

    return JsonResponse({"success": False, "errors":"", "form_html": form_html})
  


