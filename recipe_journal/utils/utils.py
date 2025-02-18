"""
General utility module with helper functions used throughout the project.

This module includes functions for managing user interactions, filtering recipes, handling collections,
and other project-specific logic.
"""
from django import forms
from django.contrib import messages
from django.db.models import Min
from django.forms import ValidationError
from django.http import JsonResponse
from recipe_journal.forms import  AddFriendForm, RecipeIngredientForm, RecipeCombinedForm
from recipe_journal.forms import ShowRecipeCollectionForm, AddRecipeToCollectionsForm, SearchRecipeForm
from recipe_journal.models import Member, Recipe, RecipeCollectionEntry
import random as rd
import spacy
import time

nlp = spacy.load("fr_core_news_sm")

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

def get_top_and_thumbnail_recipes(recipe_ids_list, top_recipe_nb):
    """
    Splits a list of recipe IDs into two querysets.

    Parameters:
    - recipe_ids_list (list): List of recipe IDs.
    - top_recipe_nb (int): Number of recipes to include in the top list.

    Returns:
    - tuple: A tuple containing:
        - QuerySet: `top_recipe_qs` with the first `top_recipe_nb` recipes.
        - QuerySet: `thumbnail_recipe_qs` with the remaining recipes.
    """
    top_recipe_qs = Recipe.objects.filter(id__in=recipe_ids_list[:top_recipe_nb])
    thumbnail_recipe_qs = Recipe.objects.filter(id__in=recipe_ids_list[top_recipe_nb:])
    
    return top_recipe_qs, thumbnail_recipe_qs

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
    Initializes and returns the forms related to the recipe.

    Parameters:
    - request (HttpRequest): The HTTP request object.

    Returns:
    - tuple: A tuple containing the recipe form, ingredient form list, and recipe action form.
    """
    recipe_ingredient_list = get_recipe_ingredient_list(request)
    recipe_ingredient_form_list = get_recipe_ingredient_form_list(recipe_ingredient_list)
    
    recipe_form = initialize_combined_form(RecipeCombinedForm, request)
    manage_collections_form = initialize_form(AddRecipeToCollectionsForm, request)
    
    return recipe_form, recipe_ingredient_form_list, manage_collections_form

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

def create_recipe_collection_entry(
        add_recipe_to_collections_form,
        collection_name,
        logged_user,
        recipe
        ):
    """
    Creates an entry in the recipe collection if the user selects the option.

    Parameters:
    - add_recipe_to_collections_form (AddRecipeToCollectionForm): The form containing user selection.
    - collection_name (str): The name of the recipe collection.
    - logged_user (Member): The currently logged-in user.
    - recipe (Recipe): The recipe to be added to the collection.

    Returns:
    - bool: True if the recipe was added to the collection, False otherwise.
    """
    action_field = AddRecipeToCollectionsForm.COLLECTION_NAME_MAPPING.get(collection_name)
    add_to_collection = add_recipe_to_collections_form.cleaned_data.get(action_field, False)

    if add_to_collection:
        RecipeCollectionEntry.objects.create(
            member=logged_user,
            recipe=recipe,
            collection_name=collection_name,
        )
        return True
    else:
        return False

def add_recipe_to_collections(add_recipe_to_collections_form, logged_user, recipe, request):
    """
    Handles adding the recipe to the user's collections if selected in the form.

    Parameters:
    - add_recipe_to_collections_form (Form): The form containing user selection.
    - logged_user (Member): The logged-in user.
    - recipe (Recipe): The recipe to add to collections.
    - request (HttpRequest): The HTTP request object.

    Returns:
    - None
    """
 
    for collection_name, collection_title in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES:
        created = create_recipe_collection_entry(
            add_recipe_to_collections_form,
            collection_name,
            logged_user,
            recipe,
        )
        if created:
            success_message = f"Recette ajoutée à votre {collection_title}"
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
    - None: Updates the user's friend list and adds a success or error message.
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
        ingredient_inputs_dict[f"ingredient_{i}"] = normalize_ingredient(ingredient_name)
        # ingredient_inputs_dict[f"ingredient_{i}"] = ingredient_name
    return ingredient_inputs_dict

def get_recipe_collection_by_sort_order(collection_name):
    """
    Retrieves recipe collection entries ordered by saving date or recipe title.

    Parameters:
    - collection_name (str): The name of the recipe collection to retrieve.

    Returns:
    - QuerySet: A queryset of RecipeCollectionEntry objects, ordered by saving date for "history",
      or by recipe title for other collections, or all entries if no collection is specified.
    """
    if collection_name == "history":
        return RecipeCollectionEntry.objects.filter(collection_name=collection_name).order_by("-saving_date")
    
    if collection_name:
        return RecipeCollectionEntry.objects.filter(collection_name=collection_name).order_by("recipe__title")
    
    return RecipeCollectionEntry.objects.all().order_by("recipe__title")

def filter_recipe_collection_by_member(recipe_collection_qs, member=None, logged_user=None):
    """
    Filters a recipe collection by the specified member or logged-in user's friends.

    Parameters:
    - recipe_collection_qs (QuerySet): The queryset of recipe collection entries to filter.
    - member (str or Member, optional): The member to filter by. If "friends", filters by logged-in user's friends.
    - logged_user (Member, optional): The currently logged-in user, required if 'member' is "friends".

    Returns:
    - QuerySet: A filtered queryset of recipe collection entries.
    
    Raises:
    - ValueError: If 'member' is "friends" and 'logged_user' is not provided.
    """
    if member == "friends" and not logged_user:
        raise ValueError("logged_user doit être défini si member == 'friends'")
    
    if not member:
        return recipe_collection_qs

    if member == "friends" and logged_user:
        friends = logged_user.friends.all()
        return recipe_collection_qs.filter(member__in=friends)

    return recipe_collection_qs.filter(member=member)

def get_filtered_recipe_collection_qs(form, logged_user=None):
    """
    Applies common filters to a recipe collection based on the form data.

    Parameters:
    - form (Form): The form containing filter data for the recipe collection.
    - logged_user (Member, optional): The currently logged-in user.

    Returns:
    - QuerySet: A filtered queryset of recipe collection entries based on the form data.
    """
    title = form.cleaned_data.get("title")
    category = form.cleaned_data.get("category")
    collection_name = form.cleaned_data.get("collection_name")
    member = form.cleaned_data.get("member")
    ingredient_inputs_dict = get_ingredient_inputs(form)

    recipe_collection_qs = get_recipe_collection_by_sort_order(collection_name)
    recipe_collection_qs = filter_recipe_collection_by_member(recipe_collection_qs, member, logged_user)

    if collection_name == "history":
        distinct_ids = recipe_collection_qs.values("recipe", "saving_date").annotate(min_id=Min("id")).values_list("min_id", flat=True)
    else:
        distinct_ids = recipe_collection_qs.values("recipe").annotate(min_id=Min("id")).values_list("min_id", flat=True)
    
    recipe_collection_qs = recipe_collection_qs.filter(id__in=distinct_ids)

    filters = {}
    if title:
        filters["recipe__title__icontains"] = title
    if category:
        filters["recipe__category"] = category

    recipe_collection_qs = recipe_collection_qs.filter(**filters)

    for ingredient_name in ingredient_inputs_dict.values():
        if ingredient_name:
            recipe_collection_qs = recipe_collection_qs.filter(recipe__recipe_ingredient__ingredient__name__icontains=ingredient_name)

    return recipe_collection_qs

def get_filtered_recipe_qs(form, logged_user):
    """
    Filters a queryset of recipes based on form data.

    Parameters:
    - form (Form): The form containing filter criteria (title, category, member, ingredients).
    - logged_user (Member): The currently logged-in user.

    Returns:
    - QuerySet: A filtered queryset of recipes based on the form data.
    """
    title = form.cleaned_data.get("title")
    category = form.cleaned_data.get("category")
    member = form.cleaned_data.get("member")
    ingredient_inputs_dict = get_ingredient_inputs(form)

    if not member:
        recipe_qs = Recipe.objects.all()
    else:
        recipe_collection_qs = RecipeCollectionEntry.objects.all().order_by("recipe__title")
        recipe_collection_qs = filter_recipe_collection_by_member(recipe_collection_qs, member, logged_user)
        recipe_ids = recipe_collection_qs.values_list("recipe", flat=True)
        recipe_qs = Recipe.objects.filter(id__in=recipe_ids)

    filters = {}
    if title:
        filters["title__icontains"] = title
    if category:
        filters["category"] = category

    recipe_qs = recipe_qs.filter(**filters)

    for ingredient_name in ingredient_inputs_dict.values():
        if ingredient_name:
            recipe_qs = recipe_qs.filter(recipe_ingredient__ingredient__name__icontains=ingredient_name)

    return recipe_qs.order_by("title")

def handle_search_recipe_request(request, logged_user):
    """
    Handles a search request for recipes based on form data.

    Parameters:
    - request (HttpRequest): The HTTP request containing the search query parameters.
    - logged_user (Member): The currently logged-in user.

    Returns:
    - tuple: A tuple containing:
        - form (Form): The validated form with the search data.
        - QuerySet: A filtered queryset of recipe collection entries if collection is selected, otherwise an empty queryset.
        - QuerySet: A filtered queryset of recipes if no collection is selected, otherwise an empty queryset.
    """
    form = SearchRecipeForm(request.GET, logged_user=logged_user)
    
    if form.is_valid():
        collection_name = form.cleaned_data.get("collection_name")

        if collection_name:
            return form, get_filtered_recipe_collection_qs(form, logged_user=logged_user), Recipe.objects.none()
        else:
            return form, RecipeCollectionEntry.objects.none(), get_filtered_recipe_qs(form, logged_user=logged_user)
   
    return form, RecipeCollectionEntry.objects.none(), Recipe.objects.all().order_by("title")

def handle_show_recipe_collection_request(request):
    """
    Handles a request to display a recipe collection based on form data.

    Parameters:
    - request (HttpRequest): The HTTP request containing the form data for the recipe collection.

    Returns:
    - tuple: A tuple containing:
        - form (Form): The validated form with the search data.
        - QuerySet: A filtered queryset of recipe collection entries based on the form data, or an empty queryset if invalid.
    """
    form = ShowRecipeCollectionForm(request.POST)

    if form.is_valid():
        return form, get_filtered_recipe_collection_qs(form)

    return form, RecipeCollectionEntry.objects.none()

def check_request_validity(request):
    """
    Validates the incoming request to check for required data and a logged-in user.

    Parameters:
    - request (HttpRequest): The HTTP request containing the form data.

    Returns:
    - tuple: A tuple containing:
        - logged_user (Member or None): The currently logged-in user, or None if not logged in.
        - recipe_id (str or None): The ID of the recipe from the request, or None if missing.
        - collection_name (str or None): The name of the collection from the request, or None if missing.
        - JsonResponse (HttpResponse or None): A JsonResponse with an error message if any validation fails, or None if valid.
    """   
    logged_user = get_logged_user(request)
    if not logged_user:
        return None, None, None, JsonResponse({"message": "Aucun utilisateur connecté."}, status=400)

    recipe_id = request.POST.get("recipe_id")
    collection_name = request.POST.get("collection_name")

    if not recipe_id:
        return None, None, None, JsonResponse({"message": "ID de recette manquant."}, status=400)
    if not collection_name:
        return None, None, None, JsonResponse({"message": "Nom de la collection manquant."}, status=400)

    if collection_name not in dict(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES):
        return None, None, None, JsonResponse({"message": f"Le modèle '{collection_name}' est inconnu."}, status=400)

    return logged_user, recipe_id, collection_name, None
 
def update_collection(request, action):
    """
    Adds or removes a recipe to/from a user's collection based on the action provided.

    Parameters:
    - request (HttpRequest): The HTTP request containing the user and recipe data.
    - action (str): The action to perform, either 'add' or 'remove'.

    Returns:
    - JsonResponse: A JSON response with a success message or error details.
        - Success message: Indicates whether the recipe was added or removed from the collection.
        - Error message: Indicates any validation errors or issues during the operation.
    """
    logged_user, recipe_id, collection_name, request_validity_error = check_request_validity(request)
    if request_validity_error:
        return request_validity_error

    try:
        collection_title = dict(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES).get(collection_name)
        if action == "add":
            _, created = RecipeCollectionEntry.objects.get_or_create(
                collection_name=collection_name,
                member=logged_user,
                recipe_id=recipe_id
                )
            message = (
                f"La recette a été ajoutée à votre {collection_title}."
                if created else
                f"La recette fait déjà partie de votre {collection_title}."
            )
        elif action == "remove":
            count, _ = RecipeCollectionEntry.objects.filter(
                collection_name=collection_name,
                member=logged_user,
                recipe_id=recipe_id
                ).delete()
            message = (
                f"La recette a été supprimée de votre {collection_title}."
                if count > 0 else
                f"La recette ne fait pas partie de votre {collection_title}."
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