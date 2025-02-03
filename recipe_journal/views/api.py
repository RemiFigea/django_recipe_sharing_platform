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
from recipe_journal.forms import AddRecipeIngredientForm, AddRecipeHistoryForm, RemoveRecipeHistoryForm
from recipe_journal.models import Member, Recipe, RecipeHistoryEntry, RecipeAlbumEntry, RecipeToTryEntry
import recipe_journal.utils.utils as ut


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
    
    title = request.GET["title"]
    error_list = ut.validate_title(title)

    if not error_list and Recipe.objects.filter(title=title).exists():
        error_list = ["Ce titre de recette est déjà utilisé!"]
    
    if error_list:
        return JsonResponse({"error_list": error_list})
    else:
        return JsonResponse({"error_list": []})
    
def add_ingredient_form(request):
    """
    Dynamically adds an ingredient form and renders it.

    Parameters:
    - request (HttpRequest): The HTTP request object.

    Returns:
    - HttpResponse: The HTML response containing the rendered ingredient form.
    """
    if request.method == "GET":
        new_form = AddRecipeIngredientForm()
        form_html = render_to_string("partials/ingredient_form.html", {"form": new_form}, request=request)
        return HttpResponse(form_html)
    else:
        return HttpResponse("Méthode non autorisée", status=405)

def check_collection_status(request):
    """
    Checks if a recipe is already in a user's collection (album, to-try, or history).

    Parameters:
    - request (HttpRequest): The HTTP request object containing recipe ID and collection model name.

    Returns:
    - JsonResponse: A response indicating whether the recipe is in the specified collection.
    """
    MODEL_MAP = {
            "RecipeAlbumEntry": RecipeAlbumEntry,
            "RecipeToTryEntry": RecipeToTryEntry,
            "RecipeHistoryEntry": RecipeHistoryEntry
        }
    logged_user = ut.get_logged_user(request)
    recipe_id = request.GET["recipe_id"]  
    model_name = request.GET["model_name"]

    if not logged_user:
        return JsonResponse({"message": "Aucun utilisateur connecté."}, status=400)
    if not recipe_id:
        return JsonResponse({"message": "ID de recette manquant."}, status=400)
    if not model_name:
        return JsonResponse({"message": "Modèle de collection manquant."}, status=400)
    
    model = MODEL_MAP.get(model_name)
    if not model:
        return JsonResponse({"message": f"Le modèle '{model_name}' est inconnu."}, status=400)

    is_in_album = model.objects.filter(member=logged_user, recipe_id=recipe_id).exists()

    return JsonResponse({"is_in_album": is_in_album})

def add_to_collection(request):
    """
    Adds a recipe to a user's collection (album, to-try, or history) if it isn't already there.

    Parameters:
    - request (HttpRequest): The HTTP request object containing recipe ID and collection model name.

    Returns:
    - JsonResponse: A response with a success message and a flag indicating whether the recipe was added.
    """
    recipe_id = request.GET["recipe_id"]  
    logged_user = ut.get_logged_user(request)
    model_name = request.GET["model_name"]
    MODEL_MAP = {
            "RecipeAlbumEntry": RecipeAlbumEntry,
            "RecipeToTryEntry": RecipeToTryEntry,
            "RecipeHistoryEntry": RecipeHistoryEntry
        }
    MODEL_TITLES = {
        "RecipeAlbumEntry": "votre album",
        "RecipeToTryEntry": "vos recettes à essayer",
        "RecipeHistoryEntry": "votre historique"
    }
   

    if not recipe_id:
        return JsonResponse({"message": "ID de recette manquant.", "created": False}, status=400)
    
    if not logged_user:
        return JsonResponse({"message": "Aucun utilisateur connecté.", "created": False}, status=400)
    
    if not model_name:
        return JsonResponse({"message": "Modèle de collection manquant."}, status=400)
    
    model_title = MODEL_TITLES.get(model_name, "la collection")
    model = MODEL_MAP.get(model_name)
    if not model:
        return JsonResponse({"message": f"Le modèle '{model_name}' est inconnu."}, status=400)

    
    try:
        _, created = model.objects.get_or_create(
            member=logged_user,
            recipe_id=recipe_id
        )

        if created:
            message = f"La recette a été ajouté à {model_title}."
        else:
            message = f"La recette fait déjà partie de {model_title}."
        
        return JsonResponse({"message": message, "created": created})
    except Exception as e:
        return JsonResponse({"message": f"Une erreur est survenue: {str(e)}", "created": False}, status=500)

def remove_from_collection(request):
    """
    Removes a recipe from a user's collection (album, to-try, or history).

    Parameters:
    - request (HttpRequest): The HTTP request object containing recipe ID and collection model name.

    Returns:
    - JsonResponse: A response with a success message and a count of how many records were deleted.
    """
    recipe_id = request.GET["recipe_id"]  
    logged_user = ut.get_logged_user(request)
    model_name = request.GET["model_name"]
    MODEL_MAP = {
            "RecipeAlbumEntry": RecipeAlbumEntry,
            "RecipeToTryEntry": RecipeToTryEntry,
            "RecipeHistoryEntry": RecipeHistoryEntry
        }
    MODEL_TITLES = {
        "RecipeAlbumEntry": "votre album",
        "RecipeToTryEntry": "vos recettes à essayer",
        "RecipeHistoryEntry": "votre historique"
    }
   

    if not recipe_id:
        return JsonResponse({"message": "ID de recette manquant.", "created": False}, status=400)
    
    if not logged_user:
        return JsonResponse({"message": "Aucun utilisateur connecté.", "created": False}, status=400)
    
    if not model_name:
        return JsonResponse({"message": "Modèle de collection manquant."}, status=400)
    
    model_title = MODEL_TITLES.get(model_name, "la collection")
    model = MODEL_MAP.get(model_name)
    if not model:
        return JsonResponse({"message": f"Le modèle '{model_name}' est inconnu."}, status=400)

    try:
        count, _ = model.objects.filter(member=logged_user, recipe_id=recipe_id).delete()

        if count > 0:
            message = f"La recette a été supprimée de {model_title}."
        else:
            message = f"La recette ne fait pas partie de {model_title}."

        return JsonResponse({"message": message, "count": count})
    except Exception as e:
        return JsonResponse({"message": "Une erreur est survenue.", "count": 0}, status=500)

def add_recipe_history(request):
    if request.method == "POST":
        form = AddRecipeHistoryForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "errors": form.errors})
    
    return HttpResponse("Méthode non autorisée", status=405)

def remove_recipe_history(request):
    if not (request.method == "POST"):
        return HttpResponse("Méthode non autorisée", status=405)

    member_id = request.POST.get("member_id")
    recipe_id = request.POST.get("recipe_id")
    print(request.POST)

    if not (member_id and recipe_id):
        return HttpResponse("Missing parameters", status=400)
    member = get_object_or_404(Member, id=member_id)
    recipe = get_object_or_404(Recipe, id=recipe_id)

    form = RemoveRecipeHistoryForm(request.POST, member=member, recipe=recipe)
    
    if form.is_valid():
        recipe_history_entry_date = form.cleaned_data["recipe_history_entry_date"]
        try:
            # if not form.fields["recipe_history_entry_date"].choices:
            #     # Si les choix sont vides, transmettre un message et ne pas afficher le formulaire
            #     return JsonResponse({"success": False, "message": "La recette ne fait pas partie de votre historique.", "form_html": ""})



            form_html = form.as_p() 
            count, _ = RecipeHistoryEntry.objects.filter(
                member=member,
                recipe=recipe,
                saving_date=recipe_history_entry_date
            ).delete()
                    
            form = RemoveRecipeHistoryForm(member=member, recipe=recipe)
            form_html = form.as_p() 
            if count > 0:
                return JsonResponse({"success": True, "form_html": form_html})
            else:
                return JsonResponse({"success": False, "errors": "Une erreur est survenue.", "form_html": form_html})

        except Exception as e:
            return JsonResponse({"success": False, "errors": "Une erreur est survenue.", "form_html": form_html}, status=500)

    form._errors.clear()
    form_html = form.as_p()


    return JsonResponse({"success": False, "errors":"", "form_html": form_html})
  


