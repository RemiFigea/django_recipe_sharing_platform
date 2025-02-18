"""Unit tests for the forms module."""

from datetime import date, timedelta
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from recipe_journal.forms import *
from recipe_journal.models import Ingredient, Member, Recipe, RecipeIngredient
import shutil
import tempfile
from unittest.mock import patch

class LoginFormTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password123"))

    def test_form_with_non_existent_username(self):
        form_data = {"username": "invalid_username", "password": "password123"}
        form = LoginForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("Identifiant ou mot de passe erroné.", form.non_field_errors())
    
    def test_form_with_invalid_password(self):
        form_data = {"username": "testuser", "password": "invalid_password"}
        form = LoginForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("Identifiant ou mot de passe erroné.", form.non_field_errors())
    
    def test_form_with_valid_login_data(self):
        form_data = {"username": "testuser", "password": "password123"}
        form = LoginForm(data=form_data)

        self.assertTrue(form.is_valid())    

class RegistrationFormTest(TestCase):
    def test_form_with_taken_username(self):
        Member.objects.create(username="testuser", password=make_password("password123"))
        form_data = {"username": "testuser", "password": "password123"}
        form = RegistrationForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn("Identifiant non disponible.", form.errors["username"])

    def test_form_with_valid_registration_data(self):
        form_data = {"username": "newuser", "password": "password123"}
        form = RegistrationForm(data=form_data)
        
        self.assertTrue(form.is_valid())

class ModifyProfileFormTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password123"))
        self.existing_member = Member.objects.create(username="existing_user", password=make_password("password123"))
    
    def test_form_with_taken_username(self):
        form_data = {
            "username": "existing_user",
            "former_password": "password123",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        form = ModifyProfileForm(data=form_data, logged_user=self.member)

        self.assertFalse(form.is_valid())
        self.assertIn("Identifiant non disponible.", form.errors["username"])

    def test_form_with_incorrect_old_password(self):
        form_data = {
            "username": "testuser",
            "former_password": "invalid_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        form = ModifyProfileForm(data=form_data, logged_user=self.member)

        self.assertFalse(form.is_valid())
        self.assertIn("Ancien mot de passe erroné.", form.errors["former_password"])
    
    
    def test_form_with_mismatched_new_password(self):
        form_data = {
            "username": "testuser",
            "former_password": "password123",
            "new_password": "new_password",
            "confirm_new_password": "invalid_new_password"
            }
        form = ModifyProfileForm(data=form_data, logged_user=self.member)

        self.assertFalse(form.is_valid())
        self.assertIn("Les nouveaux mots de passe ne correspondent pas.", form.non_field_errors())
    
    def test_form_with_multiple_valid_profile_data(self):
        test_cases = [
            {
                "desc": "same_username",
                "form_data": {
                    "username": "testuser",
                    "former_password": "password123",
                    "new_password": "new_password",
                    "confirm_new_password": "new_password"
                }
            },
            {
                "desc": "same_username_and_password",
                "form_data": {
                    "username": "testuser",
                    "former_password": "password123",
                    "new_password": "password123",
                    "confirm_new_password": "password123"
                }
            },
            {
                "desc": "new_username",
                "form_data": {
                    "username": "new_username",
                    "former_password": "password123",
                    "new_password": "password123",
                    "confirm_new_password": "password123"
                }
            },
            {
                "desc": "new_username_and_password",
                "form_data": {
                    "username": "new_username",
                    "former_password": "password123",
                    "new_password": "new_password",
                    "confirm_new_password": "new_password"
                }
            }
        ]

        for case in test_cases:
            with self.subTest(msg=case["desc"]):
                    form = ModifyProfileForm(data=case["form_data"], instance=self.member, logged_user=self.member)
                    self.assertTrue(form.is_valid())

class RecipeActionFormTest(TestCase):
    def test_form_with_valid_action_selected(self):
        form_data = {
            "add_to_history": True,
            "add_to_album": False,
            "add_to_trials": True,
        }
        form = AddRecipeToCollectionsForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["add_to_history"], True)
        self.assertEqual(form.cleaned_data["add_to_album"], False)
        self.assertEqual(form.cleaned_data["add_to_trials"], True)

class AddMainRecipeFormTest(TestCase):
    def test_form_with_valid_data(self):
        form_data = {
        "title": "Recette de test",
        "category": "dessert"
        }
        form = RecipeMainSubForm(data=form_data)
        
        self.assertTrue(form.is_valid())

    def test_form_with_taken_title(self):
        Recipe.objects.create(title="Recette de test", category="dessert")
        
        form_data = {
            "title": "Recette de test",
            "category": "entrée",
        }
        form = RecipeMainSubForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("Titre déjà utilisé.", form.errors["title"])

class AddRecipeCombinedFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir="recipe_journal/tests/test_media/temp")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.TEMP_MEDIA_ROOT)
        super().tearDownClass()

    def test_form_with_valid_recipe_data(self):
        with patch("django.conf.settings.MEDIA_ROOT", new=self.TEMP_MEDIA_ROOT):
            with open("recipe_journal/tests/test_media/image_test.jpg", "rb") as img_file:
                image = SimpleUploadedFile(
                    name="image_test.jpg",
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
            form = RecipeCombinedForm(data=form_data, files=form_files)

            self.assertTrue(form.is_valid())
            
            recipe = form.save()

            self.assertTrue(recipe in Recipe.objects.all())
            self.assertTrue("image_test.jpg" in recipe.image.name)
    
    def test_form_with_empty_data(self):
        form_data = {"title": "", "category": ""}
        form = RecipeCombinedForm(form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.main_form.errors)
        self.assertIn("category", form.main_form.errors)

class AddRecipeIngredientFormTest(TestCase):
    def test_form_with_valid_ingredient_data(self):
        form_data = {
            "name": "carotte",
            "quantity": 1.5,
            "unit": "kg"
        }
        form = RecipeIngredientForm(data=form_data)

        self.assertTrue(form.is_valid())

        recipe_ingredient = form.save()

        self.assertTrue(recipe_ingredient in RecipeIngredient.objects.all())
        self.assertTrue(recipe_ingredient.ingredient in Ingredient.objects.all())
    
    def test_form_does_not_duplicate_ingredient(self):
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
            form = RecipeIngredientForm(data=form_data)
            
            self.assertTrue(form.is_valid())
            
            form.save()
        
        self.assertTrue(len(RecipeIngredient.objects.all())==2)
        self.assertTrue(len(Ingredient.objects.all())==1)

class AddRecipeToCollectionsTest(TestCase):
    def test_form_without_action_selected(self):
        form_data = {
            "add_to_album" : False,
            "add_to_history" : False,
            "add_to_trials" : False,
        }
        form = AddRecipeToCollectionsForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("Vous devez cocher au moins une option.", form.non_field_errors())
    
    def test_form_with_valid_action_selected(self):
        form_data = {
            "add_to_album" : False,
            "add_to_history" : True,
            "add_to_trials" : True,
        }
        form = AddRecipeToCollectionsForm(data=form_data)

        self.assertTrue(form.is_valid())

class AddFriendFormTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password=make_password("password123"))
        self.friend = Member.objects.create(username="test_friend", password=make_password("password123"))

    def test_form_with_valid_username_to_add(self):
        form = AddFriendForm({"username_to_add": "test_friend"}, logged_user=self.member)

        self.assertTrue(form.is_valid())

    def test_form_with_non_existent_username_to_add(self):
        form = AddFriendForm({"username_to_add": "unvalid_username"}, logged_user=self.member)

        self.assertFalse(form.is_valid())
        self.assertIn("Aucun utilisateur trouvé avec l'identifiant 'unvalid_username'.", form.errors["username_to_add"])

    def test_form_with_already_added_friend(self):
        self.member.friends.add(self.friend)
        form = AddFriendForm({"username_to_add": "test_friend"}, logged_user=self.member)

        self.assertFalse(form.is_valid())
        self.assertIn("'test_friend' fait déjà partie de vos amis.", form.errors["username_to_add"])

class CreateRecipeHistoryFormTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password=make_password("password123"))
        self.recipe = Recipe.objects.create(title = "recette test", category = "dessert")

    def test_form_with_valid_data(self):
        form_data = {
            "member": self.member,
            "recipe": self.recipe
        }
        form = CreateRecipeHistoryForm(form_data)

        self.assertTrue(form.is_valid())
    
    def test_form_with_recipe_already_in_history(self):
        RecipeCollectionEntry.objects.create(
            collection_name = "history",
            member = self.member,
            recipe = self.recipe,
            saving_date = date.today()
        )
        form_data = {
            "member": self.member,
            "recipe": self.recipe,
            "saving_date": date.today()
        }
        form = CreateRecipeHistoryForm(form_data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            f"La recette '{self.recipe.title}' fait déjà partie de votre historique pour la date du {date.today()}!",
            form.non_field_errors()
            )
    
class DeleteRecipeHistoryFormTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password=make_password("password123"))
        self.recipe = Recipe.objects.create(title = "recette test", category = "dessert")
        self.recipe_2 = Recipe.objects.create(title = "recette test 2", category = "dessert")
        for day_delta in range(2):
            RecipeCollectionEntry.objects.create(
                collection_name = "history",
                member = self.member,
                recipe = self.recipe,
                saving_date = date.today()- timedelta(days=day_delta)
            )

    def test_form_with_valid_history_dates(self):
        form = DeleteRecipeHistoryForm({"recipe_history_entry_date": date.today()}, member=self.member, recipe=self.recipe)
        dates_set = set([date_choice[0] for date_choice in form.fields["recipe_history_entry_date"].choices])
        expected_dates_set = set([date.today() - timedelta(days=day_delta) for day_delta in range(2)])
        
        self.assertEqual(dates_set, expected_dates_set)
        self.assertTrue(form.is_valid())
    
    def test_form_with_recipe_not_in_history(self):
        form = DeleteRecipeHistoryForm({"recipe_history_entry_date": date.today()}, member=self.member, recipe=self.recipe_2)
        dates_set = set([date_choice[0] for date_choice in form.fields["recipe_history_entry_date"].choices])
        
        self.assertEqual(len(dates_set), 0)
        self.assertFalse(form.is_valid())
        self.assertIn("Select a valid choice", form.errors["recipe_history_entry_date"][0])

class SearchRecipeFormTest(TestCase):
    def test_form_with_collection_names_exluding_trials(self):
        collection_choices = dict(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES)
        for collection_name in collection_choices:
            if collection_name != "trials":
                with self.subTest():
                    form = SearchRecipeForm({"collection": collection_name})
                    
                    self.assertTrue(form.is_valid())
    
    def test_form_with_member_friends_option(self):
        form = SearchRecipeForm({"member": "friends"})

        self.assertTrue(form.is_valid())

class ShowRecipeCollectionFormTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password=make_password("password123"))
    
    def _test_form_with_valid_collection_name(self, collection_name):
        form = ShowRecipeCollectionForm({"collection_name": collection_name, "member": self.member})
        
        self.assertTrue(form.is_valid())
    
    def test_form_with_all_collection_names(self):
        for collection_name in dict(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES):
            with self.subTest(msg=collection_name):
                self._test_form_with_valid_collection_name(collection_name)

    def test_form_without_collection_name(self):
        form = ShowRecipeCollectionForm({"member": self.member})

        self.assertFalse(form.is_valid())
        self.assertIn("collection_name", form.errors)
        self.assertTrue(any("This field is required" in error_msg for error_msg in form.errors["collection_name"]))
    
    def test_form_without_member(self):
         for collection_name in dict(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES):
            with self.subTest(msg=collection_name):
                form = ShowRecipeCollectionForm({"collection_name": collection_name})

                self.assertFalse(form.is_valid())
                self.assertIn("member", form.errors)
                self.assertTrue(any("This field is required" in error_msg for error_msg in form.errors["member"]))
    
    def test_collection_name_choices_match_model(self):
        form = ShowRecipeCollectionForm()
        
        self.assertSetEqual(
            set(form.fields["collection_name"].choices),
            set(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES),
            "Les choix du formulaire ne correspondent pas exactement aux choix du modèle."
            )




    



    

