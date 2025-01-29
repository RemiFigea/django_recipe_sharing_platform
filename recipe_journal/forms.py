"""
Module containing the forms for the Django application.

Forms included:
    - LoginForm: Handles user login.
    - RegistrationForm: Manages user registration.
    - AddMainRecipeForm: Captures main recipe information like title and category.
    - AddSecondaryRecipeForm: Captures additional recipe details like cooking time and description.
    - AddRecipeCombinedForm: Combines the main and secondary recipe forms into one submission.
    - AddRecipeIngredientForm: Adds ingredients to a recipe.
    - AddFriendForm: Manages adding friends to the user's friend list.
    - RecipeActionForm: Manages actions related to adding recipes to different collections.
"""
from django import forms
from recipe_journal.models import Ingredient, Member, Rating, Recipe, RecipeIngredient

class LoginForm(forms.Form):
    """
    Form to handle user login by capturing and validating the username and password.
    """
    username = forms.CharField(label="identifiant")
    password = forms.CharField(label="mot de passe", widget = forms.PasswordInput)

    def clean(self):
        """
        Validates that the username and password match an existing user.
        """
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            result = Member.objects.filter(username=username, password=password)
            if len(result) !=1:
                raise forms.ValidationError("Identifiant ou mot de passe erroné.")
        return cleaned_data


class RegistrationForm(forms.ModelForm):
    """
    Form to handle user registration, ensuring the provided username is unique.
    """
    class Meta:
        model = Member
        fields = ["username", "password"]

    def clean(self):
        """
        Ensures the username is unique and not already taken by another user.
        """
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            result = Member.objects.filter(username=username)
            if len(result) !=0:
                raise forms.ValidationError("Identifiant non disponible.")
        return cleaned_data


class AddMainRecipeForm(forms.ModelForm):
    """
    Form to add the main details of a recipe, including title, category, source, 
    URL, and content. Ensures the recipe title is unique to avoid duplication.
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

    def clean(self):
        """
        Checks that the recipe title is unique and not already in use.
        """
        cleaned_data = super().clean()
        title = cleaned_data.get("title")

        if title:
            if Recipe.objects.filter(title=title).exists():
                raise forms.ValidationError("Titre déjà utilisé.")
            
        return cleaned_data


class AddSecondaryRecipeForm(forms.ModelForm):
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

    # RATING_CHOICES = [(None, 'Sélectionner une note')] + [(i, str(i)) for i in range(1, 6)]
    # rating = forms.ChoiceField(
    #     choices=RATING_CHOICES,
    #     required=False,
    #     widget=forms.Select(),
    # )


class AddRecipeCombinedForm(forms.Form):
    """
    A combined form for adding a recipe with both main and secondary information.
    This form includes:
        - main_form: Collects the primary details (title, category, etc.).
        - secondary_form: Collects the additional details (cooking time, short description, etc.).
    
    This form allows the submission of both sections in a single form.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_form = AddMainRecipeForm(*args, **kwargs)
        self.secondary_form = AddSecondaryRecipeForm(*args, **kwargs)

    def is_valid(self):
        return self.main_form.is_valid() and self.secondary_form.is_valid()

    def cleaned_data(self):
        return {
            "main_form": self.main_form.cleaned_data,
            "secondary_form": self.secondary_form.cleaned_data,
        }

    def save(self):
        """
        Creates and saves a new Recipe object with the main and secondary form data.
        """
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


class AddRecipeIngredientForm(forms.ModelForm):
    """
    Form to add ingredients to a recipe. 
    Ensures that the ingredient exists in the database or creates it if necessary.
    """
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
    

class AddFriendForm(forms.Form):
    """
    Form for adding a friend to the logged-in user's friend list.
    Verifies that the user exists and is not already in the friend list.
    """
    username_to_add = forms.CharField(
        label="Identifiant",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "identifiant de l'ami à ajouter"})
    )

    def __init__(self, *args, logged_user=None, **kwargs):
        self.logged_user = logged_user
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Validates that the username exists and is not already a friend of the logged-in user.
        """
        cleaned_data = super().clean()
        username_to_add = cleaned_data.get("username_to_add")

        try:
            friend = Member.objects.get(username=username_to_add)
        except Member.DoesNotExist:
            raise forms.ValidationError(f"Aucun utilisateur trouvé avec l'identifiant '{username_to_add}'.")

        if self.logged_user and self.logged_user.friends.filter(id=friend.id).exists():
            raise forms.ValidationError(f"'{username_to_add}' fait déjà partie de vos amis.")

        return cleaned_data

class RecipeActionForm(forms.Form):
    """
    Form to manage the actions of adding a recipe to various collections 
    (album, history, to-try list).
    Ensures that at least one collection is selected by the user.
    """
    add_to_album = forms.BooleanField(
        required= False,
        initial= True,
        widget=forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
        label="Ajouter la recette à mon album de recettes",
        label_suffix="",
    )
    add_to_history = forms.BooleanField(
        required= False,
        initial= False,
        widget=forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
        label="Ajouter la recette à mon historique",
        label_suffix="",
    )
    add_to_recipe_to_try = forms.BooleanField(
        required=False,
        initial= False,
        widget=forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
        label="Ajouter la recette à ma liste de recettes à essayer",
        label_suffix="",
    )

    def clean(self):
        """
        Ensures that at least one recipe collection is selected by the user.
        """
        cleaned_data = super().clean()
        add_to_album = cleaned_data.get("add_to_album")
        add_to_history = cleaned_data.get("add_to_history")
        add_to_recipe_to_try = cleaned_data.get("add_to_recipe_to_try")

        if not (add_to_album or add_to_history or add_to_recipe_to_try):
            raise forms.ValidationError("Vous devez cocher au moins une option.")
        
        return cleaned_data
