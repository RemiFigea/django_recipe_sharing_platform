"""Module for managing recipes, forms, and user interactions."""

from django.contrib import messages
from django.forms import ValidationError
from django import forms
from recipe_journal.models import Member, Recipe, RecipeAlbumEntry, RecipeHistoryEntry, RecipeToTryEntry
from recipe_journal.forms import  AddFriendForm, AddRecipeIngredientForm, AddRecipeCombinedForm, RecipeActionForm
import random as rd
import time

def get_logged_user(request):
    """
    Retrieves the logged-in user from the session.

    Parameters:
    - request (HttpRequest): The HTTP request object containing the session data.

    Returns:
    - Member: The logged-in user, or None if no user is logged in.
    """
    if "logged_user_id" in request.session:
        logged_user_id = request.session["logged_user_id"]
        return Member.objects.get(id=logged_user_id)
    else:
        return None

def get_daily_random_sample(num_samples):
    """
    Returns a stable random sample of recipe IDs based on the current date.

    Parameters:
    - num_samples (int): The number of recipes to return.

    Returns:
    - list: A list of randomly selected recipe IDs.
    """
    current_timestamp = int(time.time())
    seconds_in_a_day = 24 * 3600
    daily_timestamp = current_timestamp // seconds_in_a_day
    
    rd.seed(daily_timestamp)
    recipe_ids_list = list(Recipe.objects.values_list('id', flat=True))
    
    if len(recipe_ids_list) >= num_samples:
        random_ids = rd.sample(recipe_ids_list, min(num_samples, len(recipe_ids_list)))
        return random_ids
    else:
        return []
    
def validate_title(title):
    """
    Validates the title using Django's CharField validation.

    Parameters:
    - title (str): The title to validate.

    Returns:
    - list: A list of validation error messages if validation fails, or None if valid.
    """
    field = forms.CharField(max_length=100)
    try:
        field.clean(title)
    except ValidationError as ve:
        return ve.messages
    return None

def get_recipe_ingredient_list(request):
    """
    Extracts and validates a list of ingredients from a POST request and returns a list of dictionaries.

    Parameters:
    - request (HttpRequest): The HTTP request object containing the form data.

    Returns:
    - list: A list of dictionaries containing ingredient data.
    """
    recipe_ingredient_list = []

    if request.POST and "name" in request.POST:
        name_list = request.POST.getlist("name")
        quantity_list = request.POST.getlist("quantity")
        unit_list = request.POST.getlist("unit")

        if len(name_list) != len(quantity_list) or len(quantity_list) != len(unit_list):
            raise ValueError("List name, quantity and unit are not coherent")

        recipe_ingredient_list = [{"name": name, "quantity": quantity, "unit": unit} 
                                for name, quantity, unit in zip(name_list, quantity_list, unit_list)]

    return recipe_ingredient_list

def get_recipe_ingredient_form_list(recipe_ingredient_list):
    """
    Creates a list of recipe ingredient forms from a list of ingredient dictionaries.

    Parameters:
    - recipe_ingredient_list (list): A list of dictionaries containing ingredient data.

    Returns:
    - list: A list of form instances for each recipe ingredient.
    """
    recipe_ingredient_form_list = []

    for recipe_ingredient in recipe_ingredient_list:
        recipe_ingredient_form = AddRecipeIngredientForm(data=recipe_ingredient)
        recipe_ingredient_form_list.append(recipe_ingredient_form)
    
    if recipe_ingredient_form_list == []:
        recipe_ingredient_form_list = [AddRecipeIngredientForm()]

    return recipe_ingredient_form_list

def initialize_form(form_class, request):
    """
    Initializes and returns a form, populated with POST data if available.

    Parameters:
    - form_class (Form): The form class to instantiate.
    - request (HttpRequest): The HTTP request object containing the POST data.

    Returns:
    - Form: The initialized form instance.
    """
    form_field_names = form_class.base_fields.keys()

    if request.POST and any(field in request.POST for field in form_field_names):
        return form_class(request.POST)
    else:
        return form_class()
    
def initialize_combined_form(combined_form_class, request):
    """
    Initializes and returns a combined form with or without POST data.

    Parameters:
    - combined_form_class (Form): The combined form class to instantiate.
    - request (HttpRequest): The HTTP request object containing the POST data.

    Returns:
    - Form: The initialized combined form instance.
    """
    combined_form = combined_form_class()
    main_fields = combined_form.main_form.base_fields.keys()
    secondary_fields = combined_form.secondary_form.base_fields.keys()

    if request.POST and any(field in request.POST for field in list(main_fields) + list(secondary_fields)):
        return combined_form_class(request.POST, request.FILES)
    else:
        return combined_form_class()

def prepare_recipe_forms(request):
    """
    Initializes and returns the forms and related to the recipe.

    Parameters:
    - request (HttpRequest): The HTTP request object.

    Returns:
    - tuple: A tuple containing the recipe form, ingredient form list, and recipe action form.
    """
    recipe_ingredient_list = get_recipe_ingredient_list(request)
    recipe_ingredient_form_list = get_recipe_ingredient_form_list(recipe_ingredient_list)
    
    recipe_form = initialize_combined_form(AddRecipeCombinedForm, request)
    recipe_action_form = initialize_form(RecipeActionForm, request)
    
    return recipe_form, recipe_ingredient_form_list, recipe_action_form

def are_forms_valid(*forms):
    """
    Checks if all provided forms are valid.

    Parameters:
    - *forms: The forms to check for validity.

    Returns:
    - bool: True if all forms are valid, False otherwise.
    """
    return all(form.is_valid() for form in forms)


def save_recipe_with_ingredients(recipe_form, recipe_ingredient_form_list):
    """
    Saves a recipe and its associated ingredients.

    Parameters:
    - recipe_form (Form): The recipe form with the validated recipe data.
    - recipe_ingredient_form_list (list): A list of form instances for the recipe ingredients.

    Returns:
    - Recipe: The saved recipe object.
    """
    recipe = recipe_form.save()
    for recipe_ingredient_form in recipe_ingredient_form_list:
        recipe_ingredient = recipe_ingredient_form.save()
        recipe.recipe_ingredient.add(recipe_ingredient)
    return recipe

def add_recipe_to_collection_if_checked(
        recipe_form,
        collection_model,
        collection_field,
        logged_user,
        recipe
        ):
    """
    Adds a recipe to a collection if the user has selected to do so via the form.

    Parameters:
    - recipe_form (Form): The recipe form.
    - collection_model (Model): The collection model to add the recipe to.
    - collection_field (str): The form field name for adding to the collection.
    - logged_user (Member): The logged-in user.
    - recipe (Recipe): The recipe to add to the collection.

    Returns:
    - bool: True if the recipe was added to the collection, False otherwise.
    """

    add_to_collection = recipe_form.cleaned_data.get(collection_field, False)

    if add_to_collection:
        collection_instance = collection_model(member=logged_user, recipe=recipe)
        collection_instance.save()
        return True
    else:
        return False

def handle_recipe_collections(recipe_action_form, logged_user, recipe, request):
    """
    Handles adding the recipe to the user's collections if selected in the form.

    Parameters:
    - recipe_action_form (Form): The form for handling recipe actions.
    - logged_user (Member): The logged-in user.
    - recipe (Recipe): The recipe to add to collections.
    - request (HttpRequest): The HTTP request object.

    Returns:
    - None
    """
    collections = [
        (RecipeHistoryEntry, "add_to_history", "Recette ajoutée à l'historique de vos recettes"),
        (RecipeAlbumEntry, "add_to_album", "Recette ajoutée à votre album de recette"),
        (RecipeToTryEntry, "add_to_recipe_to_try", "Recette ajoutée à la liste de vos recettes à tester"),
    ]

    for collection_model, collection_field, success_message in collections:
        added = add_recipe_to_collection_if_checked(
            recipe_action_form,
            collection_model,
            collection_field,
            logged_user,
            recipe,
        )
        if added:
            messages.success(request, success_message)    

def handle_add_friend_request(request, logged_user):
    """
    Handles the request to add a new friend to the logged-in user's friend list.

    Parameters:
    - request (HttpRequest): The HTTP request object containing form data and user input.
    - logged_user (Member): The currently logged-in user who is attempting to add a friend.

    Returns:
    - form (AddFriendForm): The form object with validation status and error messages, if any.
    """
    form = AddFriendForm(request.GET, logged_user=logged_user)
    
    if form.is_valid():
        new_friend_username = form.cleaned_data["username_to_add"]
        
        try:
            new_friend = Member.objects.get(username=new_friend_username)
            logged_user.friends.add(new_friend)
            logged_user.save()
            messages.success(request, f"Nous avons ajouté {new_friend_username} à votre liste d'amis !")
        
        except Member.DoesNotExist:
            messages.error(request, f"Nous n'avons pas trouvé l'utilisateur {new_friend_username}. Veuillez vérifier son nom d'utilisateur.")
        
        except Exception as e:
            messages.error(request, f"Impossible d'ajouter {new_friend_username} à vos amis.")
    
    return form


def handle_remove_friend_request(request, logged_user):
    """
    Handles the request to remove a friend from the logged-in user's friend list.

    Parameters:
    - request (HttpRequest): The HTTP request object containing the form data and user input.
    - logged_user (Member): The currently logged-in user who is attempting to remove a friend.

    Returns:
    - None
    """
    friend_username = request.POST.get("username_to_remove")
    
    if friend_username:
        friend = logged_user.friends.filter(username=friend_username).first()
        
        if friend:
            try:
                logged_user.friends.remove(friend)
                logged_user.save()
                messages.success(request, f"L'utilisateur {friend_username} a été retiré de votre liste d'amis.")

            except Exception as e:
                messages.error(request, f"Une erreur s'est produite lors de la suppression de {friend_username}.")
        else:
            messages.error(request, f"L'utilisateur {friend_username} ne fait pas partie de votre liste d'amis.")
    else:
        messages.error(request, "Aucun utilisateur à supprimer.")
    
def get_recipe_entries_for_member(collection_model, member):
    """
    Returns the recipes associated with a member for a specific collection model.

    Parameters:
    - collection_model (Model): The collection model to retrieve recipes from.
    - member (Member): The member whose recipes are being retrieved.

    Returns:
    - QuerySet: A QuerySet containing the recipes for the member.
    """

    if collection_model:
        if collection_model.__name__ == "RecipeHistoryEntry":
            return collection_model.objects.filter(member=member).order_by("-saving_date")
        else:
            return collection_model.objects.filter(member=member).order_by("recipe__title")
    return None

