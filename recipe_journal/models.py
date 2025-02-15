"""
Module defining models for a recipe-sharing platform.

Models included:
    - Member: Represents a site member with authentication and friend connections.
    - Recipe: Represents a recipe with details like title, category, ingredients, and cooking times.
    - RecipeIngredient: Represents ingredients used in a recipe, including quantity and unit.
    - Ingredient: Represents a basic ingredient (e.g., flour, sugar) used in recipes.
    - BaseRecipeCollectionEntry: Abstract base class for entries in recipe collections (e.g., album, history).
    - RecipeAlbumEntry: Represents a recipe entry in a member's album.
    - RecipeToTryEntry: Represents a recipe entry in a member's "to try" list.
    - RecipeHistoryEntry: Represents a recipe entry in a member's history.
"""
from datetime import date
from django.db import models
from recipe_journal.utils.image_utils import compress_image

class Member(models.Model):
    """
    Represents a site member.

    A member can have multiple friends and has a username and password for authentication.
    """
    username = models.CharField(max_length=100, unique=True, null=False, blank=False)
    password = models.CharField(max_length=60, null=False, blank=False)
    friends = models.ManyToManyField('self', symmetrical=False, related_name='connected_to', blank=True)

class Recipe(models.Model):
    """
    Represents a recipe.

    A recipe includes title, category, source, descriptions, cooking times, ingredients, and tags.
    Images are compressed before saving.
    """
    CATEGORY_CHOICES = [
        ("entrée", "entrée"),
        ("plat", "plat principal"),
        ("dessert", "dessert"),
    ]

    title = models.CharField(max_length=100, unique=True, null=False, blank=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=False, blank=False)
    source = models.CharField(max_length=100, null=True, blank=True)
    url_link = models.CharField(max_length=100, null=True, blank=True)
    short_description = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    recipe_ingredient = models.ManyToManyField('RecipeIngredient', blank=True)
    cooking_time = models.IntegerField(null=True, blank=True)
    cooking_preparation = models.IntegerField(null=True, blank=True)
    resting_time = models.IntegerField(null=True, blank=True)
    edition_date = models.DateField(default=date.today)
    image = models.ImageField(upload_to="recipe_images/", null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Compress the image before saving if it's a new image.

        The image is only compressed if it's different from the existing one (for updates) 
        or if it's a new image (for new objects). 
        """
        if self.pk:
            old_image = Recipe.objects.filter(pk=self.pk).values_list("image", flat=True).first()
            if self.image and self.image.name != old_image:
                self.image = compress_image(self.image)
        else:
            if self.image:
                self.image = compress_image(self.image)
                
        super().save(*args, **kwargs)

class RecipeIngredient(models.Model):
    """
    Represents an ingredient in a recipe.

    Each ingredient has a quantity and a unit of measure.
    """
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    quantity = models.FloatField()
    unit = models.CharField(max_length=30)

class Ingredient(models.Model):
    """
    Represents a basic ingredient (e.g., flour, sugar).

    Can be used in multiple recipes.
    """   
    name = models.CharField(max_length=100, unique=True)

class RecipeCollectionEntry(models.Model):
    """
    Base class for recipe collection entries.

    Stores a member, recipe, saving date, and personal notes.
    """
    COLLECTION_CHOICES = [
        ("history", "historique de recettes"),
        ("album", "album de recettes"),
        ("trials", "liste de recettes à essayer")
    ]

    collection_name = models.CharField(max_length=20, choices=COLLECTION_CHOICES, null=False, blank=False, default="album")
    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    saving_date = models.DateField(default=date.today, null=False, blank=True)
    personal_note = models.TextField(null=True, blank=True)   

    def save(self, *args, **kwargs):

        if self.collection_name == "history":
            if RecipeCollectionEntry.objects.filter(
                member=self.member,
                recipe=self.recipe,
                collection_name=self.collection_name,
                saving_date=self.saving_date
            ).exists():
                raise ValueError("Cette recette a déjà été ajoutée à l'historique pour cette date.")
        elif self.collection_name in ["album", "trials"]:
                if RecipeCollectionEntry.objects.filter(
                    member=self.member,
                    recipe=self.recipe,
                    collection_name=self.collection_name
                ).exists():
                    raise ValueError(f"La recette est déjà présente dans la collection {self.collection_name}.")
        else:
            raise ValueError(f"'{self.collection_name}' n'est pas un choix valide.")
    
        super().save(*args, **kwargs)
    

    def __str__(self):
        return f'{self.recipe} in {self.collection_name} by {self.member}'



