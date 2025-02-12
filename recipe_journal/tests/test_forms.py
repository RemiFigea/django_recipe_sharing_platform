"""
Unit tests for the module forms.py.
"""
from datetime import date, timedelta
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from recipe_journal.forms import *
from recipe_journal.models import Member, Recipe, RecipeIngredient, Ingredient
import shutil
import tempfile
from unittest.mock import patch

MODEL_MAP = {
        "RecipeAlbumEntry": RecipeAlbumEntry,
        "RecipeToTryEntry": RecipeToTryEntry,
        "RecipeHistoryEntry": RecipeHistoryEntry
    }


class LoginFormTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password123"))

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
        self.member = Member.objects.create(username="testuser", password=make_password("password123"))
        self.existing_member = Member.objects.create(username="existing_user", password=make_password("password123"))
    
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
        form = ManageCollectionForm(data=form_data)
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
        form = RecipeMainSubForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_title_is_unique(self):
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
        cls.TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir="recipe_journal/tests/media/temp")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.TEMP_MEDIA_ROOT)
        super().tearDownClass()

    def test_form_valid_data(self):
        with patch("django.conf.settings.MEDIA_ROOT", new=self.TEMP_MEDIA_ROOT):
            with open("recipe_journal/tests/media/image_test.jpg", "rb") as img_file:
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
    
    def test_form_empty_data(self):
        form_data = {"title": "", "category": ""}
        form = RecipeCombinedForm(form_data)

        self.assertFalse(form.is_valid())
        self.assertIn('title', form.main_form.errors)
        self.assertIn('category', form.main_form.errors)

class AddRecipeIngredientFormTest(TestCase):
    def test_form_valid(self):
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
            form = RecipeIngredientForm(data=form_data)
            self.assertTrue(form.is_valid())
            form.save()
        
        self.assertTrue(len(RecipeIngredient.objects.all())==2)
        self.assertTrue(len(Ingredient.objects.all())==1)

class ManageCollectionFormTest(TestCase):
    def test_selected_action_missing(self):
        form_data = {
            "add_to_album" : False,
            "add_to_history" : False,
            "add_to_recipe_to_try" : False,
        }
        form = ManageCollectionForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("Vous devez cocher au moins une option.", form.non_field_errors())
    
    def test_selected_action_valid(self):
        form_data = {
            "add_to_album" : False,
            "add_to_history" : True,
            "add_to_recipe_to_try" : True,
        }
        form = ManageCollectionForm(data=form_data)

        self.assertTrue(form.is_valid())

class AddFriendFormTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password=make_password("password123"))
        self.friend = Member.objects.create(username="test_friend", password=make_password("password123"))

    def test_form_valid(self):
        form = AddFriendForm({"username_to_add": "test_friend"}, logged_user=self.member)

        self.assertTrue(form.is_valid())

    def test_form_friend_not_exists(self):
        form = AddFriendForm({"username_to_add": "unvalid_username"}, logged_user=self.member)

        self.assertFalse(form.is_valid())
        self.assertIn("Aucun utilisateur trouvé avec l'identifiant 'unvalid_username'.", form.errors["username_to_add"])

    def test_form_friend_already_in_friends(self):
        self.member.friends.add(self.friend)
        form = AddFriendForm({"username_to_add": "test_friend"}, logged_user=self.member)

        self.assertFalse(form.is_valid())
        self.assertIn("'test_friend' fait déjà partie de vos amis.", form.errors["username_to_add"])

class CreateRecipeHistoryFormTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password=make_password("password123"))
        self.recipe = Recipe.objects.create(title = "recette test", category = "dessert")

    def test_form_valid(self):
        form_data = {
            "member": self.member,
            "recipe": self.recipe
        }
        form = CreateRecipeHistoryForm(form_data)

        self.assertTrue(form.is_valid())
    
    def test_form_recipe_already_in_history(self):
        RecipeHistoryEntry.objects.create(
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
            RecipeHistoryEntry.objects.create(
                member = self.member,
                recipe = self.recipe,
                saving_date = date.today()- timedelta(days=day_delta)
            )

    def test_form_valid(self):
        form = DeleteRecipeHistoryForm({"recipe_history_entry_date": date.today()}, member=self.member, recipe=self.recipe)
        dates_set = set([date_choice[0] for date_choice in form.fields["recipe_history_entry_date"].choices])
        expected_dates_set = set([date.today() - timedelta(days=day_delta) for day_delta in range(2)])
        
        self.assertEqual(dates_set, expected_dates_set)
        self.assertTrue(form.is_valid())
    
    def test_recipe_not_in_history(self):
        form = DeleteRecipeHistoryForm({"recipe_history_entry_date": date.today()}, member=self.member, recipe=self.recipe_2)
        dates_set = set([date_choice[0] for date_choice in form.fields["recipe_history_entry_date"].choices])
        
        self.assertEqual(len(dates_set), 0)
        self.assertFalse(form.is_valid())
        self.assertIn("Select a valid choice", form.errors["recipe_history_entry_date"][0])

class SearchRecipeFormTest(TestCase):
    def test_search_recipe_collection_RecipeHistoryEntry(self):
        form = SearchRecipeForm({"collection": "RecipeHistoryEntry"})

        self.assertTrue(form.is_valid())

    def test_search_recipe_collection_RecipeAlbumEntry(self):
        form = SearchRecipeForm({"collection": "RecipeAlbumEntry"})

        self.assertTrue(form.is_valid())
    
    def test_search_recipe_member_choices_friends(self):
        form = SearchRecipeForm({"member_choices": "friends"})

        self.assertTrue(form.is_valid())

class FilterRecipeCollectionTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password=make_password("password123"))
    
    def _test_filter_recipe_form(self, model_collection_name):
        form = FilterRecipeCollectionForm({"collection": model_collection_name, "member": self.member})
        self.assertTrue(form.is_valid())
    
    def test_filter_recipe_form_cases(self):
        for model_collection_name in MODEL_MAP:
            with self.subTest():
                self._test_filter_recipe_form(model_collection_name)
                print(f"Tested {model_collection_name}")

    def test_filter_recipe_form_no_collection(self):
        form = FilterRecipeCollectionForm({"member": self.member})

        self.assertFalse(form.is_valid())
        self.assertIn("collection", form.errors)
        self.assertTrue(any("This field is required" in error_msg for error_msg in form.errors["collection"]))
    
    def test_filter_recipe_form_no_member(self):
        form = FilterRecipeCollectionForm({"collection": "RecipeToTryEntry"})

        self.assertFalse(form.is_valid())
        self.assertIn("member", form.errors)
        self.assertTrue(any("This field is required" in error_msg for error_msg in form.errors["member"]))




    



    

