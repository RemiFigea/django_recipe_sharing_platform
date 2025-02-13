"""Module for managing recipes, forms, and user interactions."""

from django import forms
from django.contrib import messages
from django.forms import ValidationError
from django.http import JsonResponse
from recipe_journal.models import Member, Recipe, RecipeAlbumEntry, RecipeHistoryEntry, RecipeToTryEntry
from recipe_journal.forms import  AddFriendForm, RecipeIngredientForm, RecipeCombinedForm
from recipe_journal.forms import FilterRecipeCollectionForm, ManageCollectionForm, SearchRecipeForm
import random as rd
# import spacy
import time

# nlp = spacy.load("fr_core_news_sm")

MODEL_MAP = {
        "RecipeAlbumEntry": RecipeAlbumEntry,
        "RecipeToTryEntry": RecipeToTryEntry,
        "RecipeHistoryEntry": RecipeHistoryEntry
    }

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
    recipe_ids_list = list(Recipe.objects.values_list("id", flat=True))
    
    if len(recipe_ids_list) > 0:
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
    Extracts and validates a list of ingredients from a POST request and returns a list of dictionaries representing the ingredients.

    Parameters:
    - request (HttpRequest): The HTTP request object containing the form data, with "name", "quantity", and "unit" fields.

    Returns:
    - A list of dictionaries, where each dictionary contains "name", "quantity", and "unit" keys representing an ingredient.
    """
    recipe_ingredient_list = []

    if "name" in request.POST:
        name_list = request.POST.getlist("name")
        quantity_list = request.POST.getlist("quantity")
        unit_list = request.POST.getlist("unit")

        if len(name_list) != len(quantity_list) or len(quantity_list) != len(unit_list):
            return recipe_ingredient_list

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
            recipe_ingredient_form = RecipeIngredientForm(data=recipe_ingredient)
            recipe_ingredient_form_list.append(recipe_ingredient_form)

    if not recipe_ingredient_form_list:
        recipe_ingredient_form_list = [RecipeIngredientForm()]

    return recipe_ingredient_form_list

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
    form_fields = list(combined_form.main_form.base_fields) + list(combined_form.secondary_form.base_fields)

    if any(field in request.POST for field in form_fields):
        return combined_form_class(request.POST, request.FILES)
    return combined_form_class()

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

    if any(field in request.POST for field in form_field_names):
        return form_class(request.POST)
    else:
        return form_class()
    
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
    
    recipe_form = initialize_combined_form(RecipeCombinedForm, request)
    manage_recipe_collection_form = initialize_form(ManageCollectionForm, request)
    
    return recipe_form, recipe_ingredient_form_list, manage_recipe_collection_form

def are_forms_valid(*forms):
    """
    Checks if all provided forms are valid.

    Parameters:
    - *forms: The forms to check for validity.

    Returns:
    - bool: True if all forms are valid, False otherwise.
    """
    return all(form.is_valid() for form in forms)

def save_recipe_and_ingredients(recipe_form, recipe_ingredient_form_list):
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
        manage_recipe_collection_form,
        model,
        logged_user,
        recipe
        ):
    """
    """
    add_to_collection = manage_recipe_collection_form.cleaned_data.get(ManageCollectionForm.MODEL_ACTION_MAPPING[model], False)

    if add_to_collection:
        recipe_collection_instance = model(member=logged_user, recipe=recipe)
        recipe_collection_instance.save()
        return True
    else:
        return False

def handle_recipe_collections(manage_recipe_collection_form, logged_user, recipe, request):
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
    for model in MODEL_MAP.values():
        added = add_recipe_to_collection_if_checked(
            manage_recipe_collection_form,
            model,
            logged_user,
            recipe,
        )
        if added:
            success_message = f"Recette ajoutée à votre {model.title}"
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
    form = AddFriendForm(request.POST, logged_user=logged_user)
    
    if form.is_valid():
        new_friend_username = form.cleaned_data["username_to_add"]
        new_friend = Member.objects.get(username=new_friend_username)

        logged_user.friends.add(new_friend)
        logged_user.save()
        messages.success(request, f"Nous avons ajouté {new_friend_username} à votre liste d'amis !")
       
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
            logged_user.friends.remove(friend)
            logged_user.save()
            messages.success(request, f"L'utilisateur {friend_username} a été retiré de votre liste d'amis.")
        else:
            messages.error(request, f"L'utilisateur {friend_username} ne fait pas partie de votre liste d'amis.")
    else:
        messages.error(request, "Aucun utilisateur à supprimer.")
       
def normalize_ingredient(ingredient_name):
    """
    Normalizes an ingredient name by lemmatizing its tokens.

    Parameters:
    - ingredient_name (str or None): The name of the ingredient to normalize.

    Returns:
    - str: The normalized ingredient name with lemmatized tokens, or None if input is None.
    """
    if ingredient_name != None:
        doc = nlp(ingredient_name)
        return " ".join([token.lemma_ for token in doc])

def get_ingredient_inputs(form):
    """
    Extracts and normalizes ingredient inputs from a form.

    Parameters:
    - form (SearchRecipeForm): The form containing ingredient input fields.

    Returns:
    - dict: A dictionary containing ingredient names, with keys formatted as "ingredient_X".
    """
    ingredient_inputs_dict = dict()

    for i in range(1, 4):
        ingredient_name = form.cleaned_data.get(f"ingredient_{i}")
        # ingredient_inputs_dict[f"ingredient_{i}"] = normalize_ingredient(ingredient_name)
        ingredient_inputs_dict[f"ingredient_{i}"] = ingredient_name
    return ingredient_inputs_dict

def filter_collection_model(collection_model_name):
    """
    """
    if MODEL_MAP.get(collection_model_name):
        return [MODEL_MAP.get(collection_model_name)]
    else:
        return [RecipeAlbumEntry, RecipeHistoryEntry]

def filter_by_member(logged_user, member, collection_model_list):
    """
    Filters recipes by member visibility (e.g., friends only).

    Parameters:
    - logged_user (Member): The currently logged-in user.
    - member (str): The visibility setting ("friends" or all members).
    - recipe_collection_qs_list (list of QuerySet): A list of QuerySets containing recipe collection objects to filter.

    Returns:
    - QuerySet: A QuerySet containing recipes objected associated to the specified member group.
    """
    if member == "friends":
        friends = logged_user.friends.all()
        recipe_collection_qs_list = [collection_model.objects.filter(member__in=friends) for collection_model in collection_model_list]
    else:
        recipe_collection_qs_list = [collection_model.objects.all() for collection_model in collection_model_list]
    recipe_ids_set = set()
    for recipe_collection_qs in recipe_collection_qs_list:
        recipe_ids_set.update(recipe_collection_qs.values_list("recipe", flat=True))
    return Recipe.objects.filter(id__in=recipe_ids_set)

def handle_search_recipe_request(request, logged_user):
    """
    Processes a recipe search request based on various filters.

    Parameters:
    - request (HttpRequest): The HTTP request containing search parameters.
    - logged_user (Member): The currently logged-in user performing the search.

    Returns:
    - tuple: A tuple containing:
        - SearchRecipeForm: The processed form with search criteria applied.
        - QuerySet: A filtered queryset of recipes matching the search criteria.
    """
    form = SearchRecipeForm(request.GET)
    recipe_entries = Recipe.objects.all()

    if form.is_valid():
        title = form.cleaned_data.get("title")
        category = form.cleaned_data.get("category")
        collection_model_name = form.cleaned_data.get("collection_name")
        member = form.cleaned_data.get("member")
        ingredient_inputs_dict = get_ingredient_inputs(form)

        collection_model_list = filter_collection_model(collection_model_name)     
        recipe_entries = filter_by_member(logged_user, member, collection_model_list)

        filters = {}
        if title:
            filters["title__icontains"] = title
        if category:
            filters["category"] = category

        recipe_entries = recipe_entries.filter(**filters)

    
        for ingredient_name in ingredient_inputs_dict.values():
            if ingredient_name:
                recipe_entries = recipe_entries.filter(recipe_ingredient__ingredient__name__icontains=ingredient_name)
        
    return form, recipe_entries

def get_member_recipe_collection_entries(collection_model, member):
    """
    Returns the recipes associated with a member for a specific collection model.

    Parameters:
    - collection_model (Model): The collection model to retrieve recipes from.
    - member (Member): The member whose recipes are being retrieved.

    Returns:
    - QuerySet: A QuerySet containing the recipes for the member.
    """  
    if collection_model.__name__ == "RecipeHistoryEntry":
        return collection_model.objects.filter(member=member).order_by("-saving_date")
    else:
        return collection_model.objects.filter(member=member).order_by("recipe__title")

def filter_member_recipe_collection(request):
    """
    Filters recipe collections based on form data.

    Parameters:
    - request (HttpRequest): The request object containing form data for filtering.

    Returns:
    - tuple: A tuple containing:
        - form (FilterRecipeCollectionForm or None): The form with the submitted data.
        - recipe_collection_entries (QuerySet or None): A QuerySet of filtered recipe collection entries.
    
    If the required elements are missing, the function returns (None, None).
    """
    recipe_collection_entries = RecipeAlbumEntry.objects.none()   
    form = FilterRecipeCollectionForm(request.POST)
    
    if form.is_valid():
        member = form.cleaned_data.get("member")
        collection_model_name = form.cleaned_data.get("collection_model_name")
        title = form.cleaned_data.get("title")
        category = form.cleaned_data.get("category")
        ingredient_inputs_dict = get_ingredient_inputs(form)
        collection_model = MODEL_MAP.get(collection_model_name)

        recipe_collection_entries =  get_member_recipe_collection_entries(collection_model, member)
        filters = {}
        if title:
            filters["recipe__title__icontains"] = title
        if category:
            filters["recipe__category"] = category

        recipe_collection_entries = recipe_collection_entries.filter(**filters)

        for ingredient_name in ingredient_inputs_dict.values():
            if ingredient_name:
                recipe_collection_entries = recipe_collection_entries.filter(recipe__recipe_ingredient__ingredient__name__icontains=ingredient_name)
   
    return form, recipe_collection_entries

def check_request_validity(request):
    """ 

    """   
    logged_user = get_logged_user(request)
    if not logged_user:
        return None, None, None, JsonResponse({"message": "Aucun utilisateur connecté."}, status=400)

    recipe_id = request.POST.get("recipe_id")
    model_name = request.POST.get("model_name")

    if not recipe_id:
        return None, None, None, JsonResponse({"message": "ID de recette manquant."}, status=400)
    if not model_name:
        return None, None, None, JsonResponse({"message": "Modèle de collection manquant."}, status=400)

    model = MODEL_MAP.get(model_name)
    if not model:
        return None, None, None, JsonResponse({"message": f"Le modèle '{model_name}' est inconnu."}, status=400)

    return logged_user, recipe_id, model, None
 
def manage_collection(request, action):
    """
    """
    logged_user, recipe_id, model, request_validity_error = check_request_validity(request)
    if request_validity_error:
        return request_validity_error

    try:
        if action == "add":
            _, created = model.objects.get_or_create(member=logged_user, recipe_id=recipe_id)
            message = (
                f"La recette a été ajoutée à votre {model.title}."
                if created else
                f"La recette fait déjà partie de votre {model.title}."
            )
        elif action == "remove":
            count, _ = model.objects.filter(member=logged_user, recipe_id=recipe_id).delete()
            message = (
                f"La recette a été supprimée de votre {model.title}."
                if count > 0 else
                f"La recette ne fait pas partie de votre {model.title}."
            )
        else:
            return JsonResponse(
                {
                    "message": "Une erreur est survenue: 'Action non valide'.",
                    "error": f"Une erreur est survenue: 'Action non valide'."
                },
                status=400
            )

        return JsonResponse({"message": message})
    except Exception as e:
        return JsonResponse(
            {
                "message": "Une erreur est survenue.",
                "error": f"Une erreur est survenue: {str(e) if e else 'Erreur inconnue'}"
            },
            status=500
        )