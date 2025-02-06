"""
Unit tests for the module forms.py.
"""
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from recipe_journal.forms import *
from recipe_journal.models import Member, Recipe, RecipeIngredient, Ingredient
import shutil
import tempfile
from unittest.mock import patch

class LoginFormTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password123"))
        self.member.save()

    def test_username_not_exists(self):
        form_data = {"username": "invalid_username", "password": "password123"}
        form = LoginForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("Identifiant ou mot de passe erroné.", form.non_field_errors())
    
    def test_password_invalid(self):
        form_data = {"username": "testuser", "password": "invalid_password"}
        form = LoginForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("Identifiant ou mot de passe erroné.", form.non_field_errors())
    
    def test_password_valid(self):
        form_data = {"username": "testuser", "password": "password123"}
        form = LoginForm(data=form_data)

        self.assertTrue(form.is_valid())    


class RegistrationFormTest(TestCase):
    def test_username_unique(self):
        Member.objects.create(username="testuser", password=make_password("password123"))
        
        form_data = {"username": "testuser", "password": "password123"}
        form = RegistrationForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn("Identifiant non disponible.", form.errors["username"])

    def test_password_valid(self):
        form_data = {"username": "newuser", "password": "password123"}
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

class ModifyProfileFormTest(TestCase):
    def setUp(self):
        Member.objects.all().delete()
        self.member = Member.objects.create(username="testuser", password=make_password("password123"))
        self.member.save()
        self.existing_member = Member.objects.create(username="existing_user", password=make_password("password123"))
        self.existing_member.save()
        
    def test_username_invalid(self):
        form_data = {
            "username": "existing_user",
            "former_password": "password123",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        form = ModifyProfileForm(data=form_data, logged_user=self.member)

        self.assertFalse(form.is_valid())
        self.assertIn("Identifiant non disponible.", form.errors["username"])

    def test_former_password_invalid(self):
        form_data = {
            "username": "testuser",
            "former_password": "invalid_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        form = ModifyProfileForm(data=form_data, logged_user=self.member)

        self.assertFalse(form.is_valid())
        self.assertIn("Ancien mot de passe erroné.", form.errors["former_password"])
    
    
    def test_new_password_invalid(self):
        form_data = {
            "username": "testuser",
            "former_password": "password123",
            "new_password": "new_password",
            "confirm_new_password": "invalid_new_password"
            }
        form = ModifyProfileForm(data=form_data, logged_user=self.member)

        self.assertFalse(form.is_valid())
        self.assertIn("Les nouveaux mots de passe ne correspondent pas.", form.non_field_errors())
    
    def test_modify_profil_success(self):
        form_data = dict()
        form_data["same_username"] = {
            "username": "testuser",
            "former_password": "password123",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        form_data["same_username_and_password"] = {
            "username": "testuser",
            "former_password": "password123",
            "new_password": "password123",
            "confirm_new_password": "password123"
            }
        form_data["new_username"] = {
            "username": "new_username",
            "former_password": "password123",
            "new_password": "password123",
            "confirm_new_password": "password123"
            }
        form_data["new_username_and_password"] = {
            "username": "new_username",
            "former_password": "password123",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        for form_dict in form_data.values():
            self.member.refresh_from_db()
            form = ModifyProfileForm(data=form_dict, instance=self.member, logged_user=self.member)
            self.assertTrue(form.is_valid())


class RecipeActionFormTest(TestCase):
    def test_form_checkboxes(self):
        form_data = {
            "add_to_history": True,
            "add_to_album": False,
            "add_to_recipe_to_try": True,
        }
        form = RecipeActionForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["add_to_history"], True)
        self.assertEqual(form.cleaned_data["add_to_album"], False)
        self.assertEqual(form.cleaned_data["add_to_recipe_to_try"], True)

class AddMainRecipeFormTest(TestCase):
    def test_form_valid(self):
        form_data = {
        "title": "Recette de test",
        "category": "dessert"
        }
        form = AddMainRecipeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_title_is_unique(self):
        Recipe.objects.create(title="Recette de test", category="dessert")
        
        form_data = {
            "title": "Recette de test",
            "category": "entrée",
        }
        form = AddMainRecipeForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("Titre déjà utilisé.", form.errors["title"])

class AddRecipeCombinedFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir="recipe_journal/tests/media/temp")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.TEMP_MEDIA_ROOT)
        super().tearDownClass()

    def test_form_valid(self):
        with patch("django.conf.settings.MEDIA_ROOT", new=self.TEMP_MEDIA_ROOT):
            with open("recipe_journal/tests/media/test_image.jpg", "rb") as img_file:
                image = SimpleUploadedFile(
                    name="test_image.jpg",
                    content=img_file.read(),
                    content_type="image/jpeg"
                )
            form_data = {
                "title": "Recette de test",
                "category": "dessert",
            }
            form_files = {
                "image": image
            }
            form = AddRecipeCombinedForm(data=form_data, files=form_files)

            self.assertTrue(form.is_valid())
            recipe = form.save()

            self.assertTrue(recipe in Recipe.objects.all())
            self.assertTrue("test_image.jpg" in recipe.image.name)

class AddRecipeIngredientFormTest(TestCase):
    def test_form_valid(self):
        form_data = {
            "name": "carotte",
            "quantity": 1.5,
            "unit": "kg"
        }
        form = AddRecipeIngredientForm(data=form_data)

        self.assertTrue(form.is_valid())

        recipe_ingredient = form.save()
        self.assertTrue(recipe_ingredient in RecipeIngredient.objects.all())
        self.assertTrue(recipe_ingredient.ingredient in Ingredient.objects.all())
    
    def test_ingredient_not_duplicated(self):
        form_data_list = [
            {
                "name": "carotte",
                "quantity": 1.5,
                "unit": "kg"
            },
            {
                "name": "carotte",
                "quantity": 3,
                "unit": "kg"
            }
        ]
        for form_data in form_data_list:
            form = AddRecipeIngredientForm(data=form_data)
            self.assertTrue(form.is_valid())
            form.save()
        
        self.assertTrue(len(RecipeIngredient.objects.all())==2)
        self.assertTrue(len(Ingredient.objects.all())==1)

class AddRecipeActionFormTest(TestCase):
    def test_selected_action_missing(self):
        form_data = {
            "add_to_album" : False,
            "add_to_history" : False,
            "add_to_recipe_to_try" : False,
        }
        form = RecipeActionForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("Vous devez cocher au moins une option.", form.non_field_errors())
    
    def test_selected_action_valid(self):
        form_data = {
            "add_to_album" : False,
            "add_to_history" : True,
            "add_to_recipe_to_try" : True,
        }
        form = RecipeActionForm(data=form_data)

        self.assertTrue(form.is_valid())





    

