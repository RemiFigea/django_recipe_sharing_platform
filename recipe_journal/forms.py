"""
Module containing various forms used for filtering, displaying, and manipulating recipe data.

Each form in this module serves as a structured input interface for interacting with the application's data models and views.
"""
from django.contrib.auth.hashers import check_password, make_password
from django import forms
from recipe_journal.models import Ingredient, Member, Recipe, RecipeCollectionEntry, RecipeIngredient

class LoginForm(forms.Form):
    """Form to handle user login by capturing and validating the username and password."""

    username = forms.CharField(label="identifiant", required=True)
    password = forms.CharField(label="mot de passe", widget = forms.PasswordInput, required=True)

    def clean(self):
        """Validates that the username and password match an existing user."""

        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            try:
                user = Member.objects.get(username=username)
            except Member.DoesNotExist:
                raise forms.ValidationError("Identifiant ou mot de passe erroné.")

            if not check_password(password, user.password):
                raise forms.ValidationError("Identifiant ou mot de passe erroné.")
        return cleaned_data

class RegistrationForm(forms.ModelForm):
    """Form to handle user registration, ensuring the provided username is unique."""

    class Meta:
        model = Member
        fields = ["username", "password"]
        labels = {
            "username": "identifiant",
            "password": "mot de passe",
        }
        widgets = {"password": forms.PasswordInput()}

    def clean_username(self):
        """Ensures the username is unique and not already taken by another user."""

        username = self.cleaned_data.get("username")

        if username:
            if Member.objects.filter(username=username).exists():
                raise forms.ValidationError("Identifiant non disponible.")
        return username
    
    def save(self, commit=True):
        """Saves the new user after hashing the password."""

        member = super().save(commit=False)
        password = self.cleaned_data["password"]

        if password:
            member.password = make_password(password)

        if commit:
            member.save()

        return member
    
class ModifyProfileForm(forms.ModelForm):
    """Form to modify the user's profile, including username and password update."""

    former_password = forms.CharField(
        label="Ancien mot de passe",
        widget=forms.PasswordInput(),
        required=True
    )
    new_password = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(),
        required=True
    )
    confirm_new_password = forms.CharField(
        label="Confirmez le nouveau mot de passe",
        widget=forms.PasswordInput(),
        required=True
    )

    class Meta(RegistrationForm.Meta):
        model = Member
        fields = ["username", "former_password", "new_password", "confirm_new_password"]
        labels = {
            "username": "Identifiant",
        }
        edit_only = True

    def __init__(self, *args, logged_user=None, **kwargs):
        """
        Initializes the form with the logged-in user's information.

        Parameters:
        - logged_user (Member): The currently logged-in user attempting to modify their profile.
        """
        self.logged_user = logged_user
        super().__init__(*args, **kwargs)

    def clean_username(self):
        """Validates that the username is either unchanged or unique."""

        username = self.cleaned_data.get("username")

        if username and username != self.logged_user.username:
            if Member.objects.filter(username=username).exists():
                raise forms.ValidationError("Identifiant non disponible.")
        return username

    def clean_former_password(self):
        """Validates that the former password matches the stored password."""

        former_password = self.cleaned_data.get("former_password")

        if not check_password(former_password, self.logged_user.password):
            raise forms.ValidationError("Ancien mot de passe erroné.")
        return former_password
    
    def clean(self):
        """Validates that the new password and confirmation match."""

        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if new_password != confirm_new_password:
            raise forms.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        return cleaned_data

    
    def save(self, commit=True):
        """Saves the modified profile with the new username and password."""

        username = self.cleaned_data["username"]
        new_password = self.cleaned_data["new_password"]

        member = self.logged_user
        member.username = username

        if new_password:
            member.password = make_password(new_password)

        if commit:
            member.save()

        return member

class RecipeMainSubForm(forms.ModelForm):
    """
    Form to add the main details of a recipe, including title, category, source,
    URL, and content.
    """
    class Meta:
        model = Recipe
        fields = [
            "title",
            "category",
            "source",
            "url_link",
            "content",
            ]
        labels = {
            "title": "Titre de la recette",
            "category": "Catégorie",
            "source": "Source de la recette",
            "url_link": "Lien vers site web",
            "content": "Etapes de la recette",
        }
        widgets = {
            "title": forms.TextInput(attrs={"id": "id_title", "placeholder": "champs obligatoire",}, ),
            "category": forms.Select(),
            "source": forms.TextInput(attrs={"placeholder": "magazine, livre de cuisine, site web ...",}, ),
            "url_link": forms.URLInput(attrs={"placeholder": "Lien vers la recette"}),
            "content": forms.Textarea(attrs={"placeholder": "Écrire ou copier/coller les étapes de la recette ici ..."}),
        }

    def clean_title(self):
        """Checks that the recipe title is unique and not already in use."""

        title = self.cleaned_data.get("title")

        if title:
            if Recipe.objects.filter(title=title).exists():
                raise forms.ValidationError("Titre déjà utilisé.")
            
        return title

class RecipeSecondarySubForm(forms.ModelForm):
    """
    Form to add secondary details of a recipe, such as cooking time, preparation time, 
    resting time, and a short description.
    """
    class Meta:
        model = Recipe
        fields = [
            "image",
            "cooking_time",
            "cooking_preparation",
            "resting_time",
            "short_description",
            ]
        labels = {
            "image": "Photo du plat",
            "cooking_time": "Temps de cuisson (en minutes)",
            "cooking_preparation": "Temps de préparation (en minutes)",
            "resting_time": "Temps de repos (en minutes)",
            "short_description": "courte présentation",
        }

class RecipeCombinedForm(forms.Form):
    """
    A combined form for adding a recipe with both main and secondary information.
    This form includes:
        - main_form: Collects the primary details (title, category, etc.).
        - secondary_form: Collects the additional details (cooking time, short description, etc.).
    
    This form allows the submission of both sections in a single form.
    """
    def __init__(self, *args, **kwargs):
        """Initializes the combined form with main and secondary subforms."""

        super().__init__(*args, **kwargs)
        self.main_form = RecipeMainSubForm(*args, **kwargs)
        self.secondary_form = RecipeSecondarySubForm(*args, **kwargs)

    def is_valid(self):
        """Validates both the main and secondary forms."""

        main_valid = self.main_form.is_valid()
        secondary_valid = self.secondary_form.is_valid()

        return main_valid and secondary_valid

    def clean(self):
        """Cleans and combines the cleaned data from both forms."""

        return {
            "main_form": self.main_form.cleaned_data,
            "secondary_form": self.secondary_form.cleaned_data,
        }

    def save(self):
        """Creates and saves a new Recipe object with the form data."""

        title = self.main_form.cleaned_data["title"]
        category = self.main_form.cleaned_data["category"]
        source = self.main_form.cleaned_data["source"]
        url_link = self.main_form.cleaned_data["url_link"]
        content = self.main_form.cleaned_data["content"]
        image = self.secondary_form.cleaned_data["image"]
        cooking_time = self.secondary_form.cleaned_data["cooking_time"]
        cooking_preparation = self.secondary_form.cleaned_data["cooking_preparation"]
        resting_time = self.secondary_form.cleaned_data["resting_time"]
        short_description = self.secondary_form.cleaned_data["short_description"]
        
        recipe = Recipe(
            title=title,
            category=category,
            source=source,
            url_link=url_link,
            content=content,
            image=image,
            cooking_time=cooking_time,
            cooking_preparation=cooking_preparation,
            resting_time=resting_time,
            short_description=short_description
        )
        recipe.save()

        return recipe

class RecipeIngredientForm(forms.ModelForm):
    """Form to add ingredients to a recipe."""

    name = forms.CharField(
        max_length=100,
        label="nom de l'ingrédient",
        widget=forms.TextInput(attrs={
            "placeholder": "nom de l\'ingrédient...",
            "class": "ingredient-autocomplete"
        })
    )

    class Meta:
        model = RecipeIngredient
        fields = [
            "quantity",
            "unit",
            ]
        labels = {
            "quantity": "quantité",
            "unit": "unité de mesure",
        }
    field_order = ["name", "quantity", "unit"]

    def save(self, commit=True):
        """
        Saves the ingredient, creating it if it doesn't exist, and associates it with the recipe.
        """
        cleaned_data = self.cleaned_data
        name = cleaned_data.get('name')

        ingredient, created = Ingredient.objects.get_or_create(name=name)

        instance = super().save(commit=False)
        instance.ingredient = ingredient

        if commit:
            instance.save()

        return instance
    
class AddRecipeToCollectionsForm(forms.Form):
    """
    Form to manage the actions of adding a recipe to various collections 
    (album, history, trials).
    """
    COLLECTION_NAME_MAPPING = {
        "album": "add_to_album",
        "history": "add_to_history",
        "trials": "add_to_trials"        
    }

    add_to_album = forms.BooleanField(
        required= False,
        initial= True,
        widget=forms.CheckboxInput,
        label="Ajouter la recette à mon album de recettes",
        label_suffix="",
    )
    add_to_history = forms.BooleanField(
        required= False,
        initial= False,
        widget=forms.CheckboxInput,
        label="Ajouter la recette à mon historique",
        label_suffix="",
    )
    add_to_trials = forms.BooleanField(
        required=False,
        initial= False,
        widget=forms.CheckboxInput,
        label="Ajouter la recette à ma liste de recettes à essayer",
        label_suffix="",
    )

    def clean(self):
        """Ensures that at least one recipe collection is selected by the user."""

        cleaned_data = super().clean()
        add_to_album = cleaned_data.get("add_to_album")
        add_to_history = cleaned_data.get("add_to_history")
        add_to_trials = cleaned_data.get("add_to_trials")

        if not (add_to_album or add_to_history or add_to_trials):
            raise forms.ValidationError("Vous devez cocher au moins une option.")
        
        return cleaned_data
    
class AddFriendForm(forms.Form):
    """Form for adding a friend to the logged-in user's friend list."""

    username_to_add = forms.CharField(
        label="Identifiant",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "identifiant de l'ami à ajouter"})
    )

    def __init__(self, *args, logged_user=None, **kwargs):
        """
        Initializes the form with the logged-in user's information.

        Parameters:
        - logged_user (Member): The currently logged-in user attempting to modify their profile.
        """
        self.logged_user = logged_user
        super().__init__(*args, **kwargs)

    def clean_username_to_add(self):
        """Validates that the username exists and is not already a friend of the logged-in user."""

        cleaned_data = super().clean()
        username_to_add = cleaned_data.get("username_to_add")

        try:
            friend = Member.objects.get(username=username_to_add)
        except Member.DoesNotExist:
            raise forms.ValidationError(f"Aucun utilisateur trouvé avec l'identifiant '{username_to_add}'.")

        if self.logged_user and self.logged_user.friends.filter(id=friend.id).exists():
            raise forms.ValidationError(f"'{username_to_add}' fait déjà partie de vos amis.")

        return username_to_add

class CreateRecipeHistoryForm(forms.ModelForm):
    """Form to create a new recipe collection entry in the user's history collection."""

    class Meta:
        model = RecipeCollectionEntry
        fields = ["collection_name", "member", "recipe", "saving_date", "personal_note"]
    
    def __init__(self, *args, **kwargs):
        """Initializes the form and sets 'history' as the default collection name."""

        super().__init__(*args, **kwargs)
        self.fields["collection_name"].initial = "history"
        self.fields["collection_name"].widget = forms.HiddenInput()
        self.fields["collection_name"].required = False

    def clean(self):
        """
        Validates that the recipe isn't already part of the user's history for the given date.
        """
        cleaned_data = super().clean()
        cleaned_data["collection_name"] = "history"
        saving_date = cleaned_data.get("saving_date")
        member = cleaned_data.get("member")
        recipe = cleaned_data.get("recipe")

        if RecipeCollectionEntry.objects.filter(
            collection_name="history",
            member=member,
            recipe=recipe,
            saving_date=saving_date
        ).exists():
            raise forms.ValidationError(f"La recette '{recipe.title}' fait déjà partie de votre historique pour la date du {saving_date}!")
        
        return cleaned_data

class DeleteRecipeHistoryForm(forms.Form):
    """
    Form to delete a recipe entry from the user's history by selecting a specific date.
    """

    def __init__(self, *args, member=None, recipe=None, **kwargs):
        """
        Initializes the form and populates the date choices for the given member and recipe.

        Parameters:
        - member (Member, optional): The logged-in user or member whose history is being modified.
        - recipe (Recipe, optional): The recipe for which the history entry is being modified.
        """
        super().__init__(*args, **kwargs)
        self.member = member
        self.recipe = recipe
        self.date_choices = []

        if member and recipe:
            queryset = RecipeCollectionEntry.objects.filter(collection_name="history", member=member, recipe=recipe)
            dates = queryset.values_list("saving_date", flat=True).distinct()
            self.date_choices = [(date, date.strftime("%Y-%m-%d")) for date in dates]

        self.fields["recipe_history_entry_date"] = forms.ChoiceField(
            choices=self.date_choices,
            label="Choisir une date",
            required=True
        )

class BaseFilterRecipeForm(forms.Form):
    """
    Base form class for filtering recipes based on various optional criteria, 
    including title, category, and ingredients.
    """
    title = forms.CharField(label="titre de la recette:", required=False)
    category = forms.ChoiceField(
        label="type de plat:",
        choices=[("", "tous")] + Recipe.CATEGORY_CHOICES,
        required=False
    )
    ingredient_1 = forms.CharField(label="ingredient 1:", required=False)
    ingredient_2 = forms.CharField(label="ingredient 2:", required=False)
    ingredient_3 = forms.CharField(label="ingredient 3:", required=False)

class SearchRecipeForm(BaseFilterRecipeForm):
    """
    Form for filtering recipes based on their collection name and various optional criteria such as title, 
    category, and ingredients.
    
    In addition to the optional criteria in the base form, this form allows filtering by:
    - "collection_name": The collection to filter recipes by, excluding the 'trials' collection.
    - "member": An optional field to filter by logged-in user's friends.
    """

    FORM_COLLECTION_CHOICES = [("", "toutes")] + [
        (key, value) for key, value in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES if key != "trials"
    ]
    MEMBER_CHOICES = [
        ("", "tous"),
        ("friends", "mes amis"),
    ]

    collection_name = forms.ChoiceField(label="collection:", choices=FORM_COLLECTION_CHOICES, required=False)

    def __init__(self, *args, logged_user=None, **kwargs):
        """
        Initializes the form with options to filter recipes based on various criteria.

        Parameters:
        - logged_user (Member, optional): The currently logged-in user who may have specific filtering options, like friends.

        Updates the form fields based on the provided logged_user:
        - If logged_user is provided, adds a 'member' field to the form, allowing filtering by members (e.g., friends).
        """
        self.logged_user = logged_user
        super().__init__(*args, **kwargs)
        
        if logged_user:
            self.fields["member"] = forms.ChoiceField(label="membres:", choices=self.MEMBER_CHOICES, required=False)

class ShowRecipeCollectionForm(BaseFilterRecipeForm):
    """
    Form to filter and display a recipe collection based on its name and a specified member.

    In addition to the optional criteria in the base form, this form allows filtering by:
    - "collection_name": The collection to display.
    - "member": A member whose collection is being viewed.
    """
    collection_name = forms.ChoiceField(
        label="collection:",
        choices=RecipeCollectionEntry.MODEL_COLLECTION_CHOICES,
        required=True
    )
    member = forms.ModelChoiceField(
        label="membre",
        queryset=Member.objects.all(),
        required=True
    )
    