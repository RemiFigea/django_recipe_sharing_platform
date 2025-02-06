"""
Unit tests for the module models.py.
"""
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
    def test_username_unique(self):
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

    def test_title_unique(self):
        Recipe.objects.create(title="recipe_title", category="entrée")

        self.assertTrue(Recipe.objects.filter(title="recipe_title", category="entrée").exists())
        
        with self.assertRaises(IntegrityError):
            Recipe.objects.create(title="recipe_title", category="plat") 
    
    def test_image_compressed_only_one_time(self):
        with patch("django.conf.settings.MEDIA_ROOT", new=self.TEMP_MEDIA_ROOT):
            with open("recipe_journal/tests/media/test_image.jpg", "rb") as img_file:
                image = SimpleUploadedFile(
                    name="test_image.jpg",
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
            self.assertTrue("test_image.jpg" in recipe.image.name)

            recipe.image = image
            recipe.save()

            image_weight_after_second_saving = os.path.getsize(recipe.image.path)

            self.assertTrue(
                image_weight_after_saving == image_weight_after_second_saving,
                "L'image ne devrait pas avoir été compressée à nouveau."
                )




        
