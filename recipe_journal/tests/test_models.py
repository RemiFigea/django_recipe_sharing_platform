"""
Unit tests for the models.py module.
"""
from datetime import date
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
import os
from recipe_journal.models import *
import shutil
import tempfile
from unittest.mock import patch

class MemberModelTest(TestCase):
    def test_model_username_must_be_unique(self):
        Member.objects.create(username="testuser", password=make_password("password123"))
        
        with self.assertRaises(IntegrityError):
            Member.objects.create(username="testuser", password=make_password("newpassword123"))

class RecipeModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir="recipe_journal/tests/media/temp")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.TEMP_MEDIA_ROOT)
        super().tearDownClass()

    def test_model_title_must_be_unique(self):
        Recipe.objects.create(title="recipe_title", category="entrée")

        self.assertTrue(Recipe.objects.filter(title="recipe_title", category="entrée").exists())
        with self.assertRaises(IntegrityError):
            Recipe.objects.create(title="recipe_title", category="plat") 
    
    def test_model_image_is_compressed_only_once(self):
        with patch("django.conf.settings.MEDIA_ROOT", new=self.TEMP_MEDIA_ROOT):
            with open("recipe_journal/tests/media/image_test.jpg", "rb") as img_file:
                image = SimpleUploadedFile(
                    name="image_test.jpg",
                    content=img_file.read(),
                    content_type="image/jpeg"
                )

            initial_image_weight = len(image.read())
            recipe = Recipe.objects.create(
                title="recipe_title",
                category="entrée",
                image=image
                )
            
            image_weight_after_saving = os.path.getsize(recipe.image.path)

            self.assertTrue(
                image_weight_after_saving < initial_image_weight,
                "L'image devrait avoir été compressée."
                )
            self.assertTrue(recipe in Recipe.objects.all())
            self.assertTrue("image_test.jpg" in recipe.image.name)

            recipe.image = image
            recipe.save()
            image_weight_after_second_saving = os.path.getsize(recipe.image.path)

            self.assertTrue(
                image_weight_after_saving == image_weight_after_second_saving,
                "L'image ne devrait pas avoir été compressée à nouveau."
                )

class IngredientModelTest(TestCase):
    def test_model_with_valid_name(self):
        ingredient = Ingredient.objects.create(name="Sugar")

        self.assertTrue(ingredient.name == "Sugar")

    def test_model_name_must_be_unique(self):
        Ingredient.objects.create(name="Sugar")
        
        with self.assertRaises(IntegrityError):
            Ingredient.objects.create(name="Sugar")

class RecipeIngredientModelTest(TestCase):
    def setUp(self):
        Ingredient.objects.create(name="Flour")

    def test_model_valid_data(self):
        ingredient = Ingredient.objects.get(name="Flour")
        recipe_ingredient = RecipeIngredient.objects.create(
            ingredient=ingredient, quantity=2.5, unit="cups"
        )

        self.assertTrue(recipe_ingredient.ingredient.name == "Flour")
        self.assertTrue(recipe_ingredient.quantity == 2.5)
        self.assertTrue(recipe_ingredient.unit == "cups")
    
    def test_model_cascade_delete_on_ingredient(self):
        ingredient = Ingredient.objects.get(name="Flour")
        RecipeIngredient.objects.create(
            ingredient=ingredient, quantity=2.5, unit="cups"
        )

        self.assertTrue(len(RecipeIngredient.objects.all()) == 1)

        Ingredient.objects.filter(name="Flour").delete()

        self.assertTrue(len(RecipeIngredient.objects.all()) == 0)
        
class IngredientModelTest(TestCase):
    def test_model_valid_name(self):
        Ingredient.objects.create(name="jambon")

        self.assertTrue(Ingredient.objects.filter(name="jambon").exists())
    
    def test_model_name_must_be_unique(self):
        Ingredient.objects.create(name="jambon")

        with self.assertRaises(IntegrityError):
            Ingredient.objects.create(name="jambon")

class RecipeCollectionModelTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password123"))
        self.recipe = Recipe.objects.create(title="recipe_title", category="entrée")
    
    def test_model_valid_data(self):
        for collection_name, _ in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES:
            
            with self.subTest(msg=collection_name):
                form_data = {
                    "collection_name": collection_name,
                    "member": self.member,
                    "recipe": self.recipe,
                }

                recipe_collection = RecipeCollectionEntry.objects.create(**form_data)

                self.assertTrue(RecipeCollectionEntry.objects.filter(**form_data).exists())
                self.assertEqual(recipe_collection.saving_date, date.today())
    
    def test_model_invalid_data(self):
        test_cases = [
            {
                "desc": "invalid_collection_name",
                "partial_form_data":  {"collection_name": "invalid_collection_name"}
            },
            {
                "desc": "invalid_saving_date",
                "partial_form_data":  {"saving_date": "invalid_saving_date"}
            },

        ]
        for case in test_cases:
            with self.subTest(msg=case["desc"]):
                form_data = {
                    "member": self.member,
                    "recipe": self.recipe,
                    **case["partial_form_data"]
                }
            
                with self.assertRaises(Exception) as e:
                    RecipeCollectionEntry.objects.create(**form_data)

        





