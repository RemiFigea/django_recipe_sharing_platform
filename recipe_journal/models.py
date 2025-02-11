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

class BaseRecipeCollectionEntry(models.Model):
    """
    Base class for recipe collection entries.

    Stores a member, recipe, saving date, and personal notes.
    """
    # COLLECTION_TYPES = [
    #     ("history", "Historique de recettes"),
    #     ("album", "Album de recettes"),
    #     ("trials", "Recettes à essayer")
    # ]

    # collection_type = models.CharField(max_length=20, choices=COLLECTION_TYPES)
    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    saving_date = models.DateField(default=date.today, null=False, blank=True)
    personal_note = models.TextField(null=True, blank=True)

    def get_collection_name(self):
        return self.__class__.__name__

    class Meta:
        abstract = True

class RecipeAlbumEntry(BaseRecipeCollectionEntry):
    """
    Represents an entry in a member's recipe album.
    """
    title = "album de recettes"

class RecipeToTryEntry(BaseRecipeCollectionEntry):
    """
    Represents an entry in a member's list of recipes to try.
    """
    title = "liste de recettes à essayer"

class RecipeHistoryEntry(BaseRecipeCollectionEntry):
    """
    Represents an entry in a member's recipe history.
    """
    title = "historique de recettes"

class Comment(models.Model):
    """
    Represents a comment by a member on a recipe.

    Includes the comment content and publication date.
    """
    author = models.ForeignKey("Member", on_delete=models.PROTECT)
    recipe = models.ForeignKey("Recipe", on_delete=models.CASCADE)
    content = models.TextField()
    publication_date = models.DateField()

