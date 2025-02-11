"""
Unit tests for the views Django contained in the module api.py..
"""
from datetime import date
from django.http import HttpResponse, JsonResponse
from django.test import TestCase
from django.urls import reverse
from recipe_journal.models import Member, Recipe, RecipeAlbumEntry, RecipeToTryEntry, RecipeHistoryEntry
from recipe_journal.tests.test_config.mock_function_paths import MockFunctionPathManager
import recipe_journal.utils.utils as ut
from unittest.mock import MagicMock, patch, PropertyMock

path = MockFunctionPathManager()

MODEL_MAP = {
        "RecipeAlbumEntry": RecipeAlbumEntry,
        "RecipeToTryEntry": RecipeToTryEntry,
        "RecipeHistoryEntry": RecipeHistoryEntry
    }

class CheckTitleTest(TestCase):
    def check_status_code_200_error_list(self, params, expected_message_list):
        response = self.client.get(reverse("check_title"), params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["error_list"], expected_message_list)

    def test_check_title_method_post(self):
        response = self.client.post(reverse("check_title"))

        self.assertEqual(response.status_code, 405)

    def test_check_title_absent(self):
        response = self.client.get(reverse("check_title"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "'title' absent de l'objet request.")

    @patch.object(ut, path.VALIDATE_TITLE)
    def test_check_title_valid(self, mock_validate_title):
        mock_validate_title.return_value = None

        self.check_status_code_200_error_list(
            params={"title": "recette test"},
            expected_message_list=[]
            )

    @patch.object(ut, path.VALIDATE_TITLE)
    def test_check_title_already_exists(self, mock_validate_title):
        mock_validate_title.return_value = None
        Recipe.objects.create(title="recette test")

        self.check_status_code_200_error_list(
            params={"title": "recette test"},
            expected_message_list=["Ce titre de recette est déjà utilisé!"]
            )

    @patch.object(ut, path.VALIDATE_TITLE)
    def test_check_title_invalid_format(self, mock_validate_title):
        mock_validate_title.return_value = ["Titre trop long"]
        
        self.check_status_code_200_error_list(
            params={"title": 30*"title trop long"},
            expected_message_list=["Titre trop long"]
            )

class AddIngredientFormTest(TestCase):
    def test_add_ingredient_form_mehtod_post(self):
        response = self.client.post(reverse("add_ingredient_form"))

        self.assertEqual(response.status_code, 405)

    def test_add_ingredient_form_success(self):
        response = self.client.get(reverse("add_ingredient_form"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("form_html", response.json())

        form_html = response.json()["form_html"]
        
        self.assertTrue(len(form_html) > 0)
        self.assertIn('id="form-recipe-ingredient"', form_html)

class CheckCollectionStatusTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.recipe = Recipe.objects.create(title="recette test", category="plat")
    
    @patch.object(ut, path.CHECK_REQUEST_VALIDITY)
    def check_collection_status_error_response(self, mock_check_request_validity):
        mock_check_request_validity.return_value= None, None, None, "mocked_error_response"
        response = self.client.post(reverse("check_collection_status"))

        self.assertEqual(response, "mocked_error_response")

    @patch.object(ut, path.CHECK_REQUEST_VALIDITY)
    def check_recipe_is_in_collection(self, mock_check_request_validity,  model, expected_result):
        mock_check_request_validity.return_value= self.member, self.recipe.id, model, None
        response = self.client.post(reverse("check_collection_status"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["is_in_collection"], expected_result)  

    
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_check_collection_is_in_collection_True(self, mock_get_logged_user):
        mock_get_logged_user.return_value =  self.member

        for model in MODEL_MAP.values():
            model.objects.create(member=self.member, recipe=self.recipe)
            self.check_recipe_is_in_collection(model=model, expected_result=True)

    @patch.object(ut, path.GET_LOGGED_USER)
    def test_check_collection_is_in_collection_False(self, mock_get_logged_user):
        mock_get_logged_user.return_value =  self.member

        for model in MODEL_MAP.values():
            self.check_recipe_is_in_collection(model=model, expected_result=False)

class ManageCollectionTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.recipe = Recipe.objects.create(title="recette test", category="plat")
    
    def test_manage_collection_method_get(self):
        for url_name in ["add_to_collection", "remove_from_collection"]:
            response = self.client.get(reverse(url_name))

            self.assertEqual(response.status_code, 405)
    
    def test_manage_collection_called(self):
        for url_name, action in ("add_to_collection", "add"), ("remove_from_collection", "remove"):
            with patch.object(ut, path.MANAGE_COLLECTION) as mock_manage_collection:
                mock_manage_collection.return_value = HttpResponse(status=200)
                response = self.client.post(reverse(url_name))
                
                mock_manage_collection.assert_called_once_with(response.wsgi_request, action)
                self.assertEqual(response.status_code, 200)

class AddRecipeHistoryTest(TestCase):
	def setUp(self):
		self.member = Member.objects.create(username="test_user", password="password")
		self.recipe = Recipe.objects.create(title="recette test", category="plat")
        
	def test_add_recipe_history_method_get(self):
		response = self.client.get(reverse("add_recipe_history"))
		self.assertEqual(response.status_code, 405)

	def test_add_recipe_history_form_valid(self):
		form_data = {
		"member": self.member.id,
		"recipe": self.recipe.id,
		}
		response = self.client.post(reverse("add_recipe_history"), form_data)

		self.assertEqual(response.status_code, 200)
		self.assertIn("success", response.json())
		self.assertTrue( response.json()["success"])

	def test_add_recipe_history_form_invalid(self):
		response = self.client.post(reverse("add_recipe_history"), {"member": self.member.id})

		self.assertEqual(response.status_code, 200)
		self.assertIn("success", response.json())
		self.assertFalse( response.json()["success"])
		self.assertIn("errors", response.json())

class RemoveRecipeHistoryTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.recipe = Recipe.objects.create(title="recette test", category="plat")
        
    def test_remove_recipe_history_method_get(self):
        response = self.client.get(reverse("remove_recipe_history"))

        self.assertEqual(response.status_code, 405)
    
    def test_remove_recipe_history_date_invalid(self):
        form_data = {
            "member": self.member.id,
            "recipe": self.recipe.id,
            "recipe_history_entry_date": date.today()
            }
        response = self.client.post(reverse("remove_recipe_history"), form_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json())
        self.assertFalse( response.json()["success"])
        self.assertIn("errors", response.json())
        self.assertEqual(response.json()["errors"], "")
        self.assertIn("form_html", response.json())
        self.assertIn("recipe_history_entry_date", response.json()["form_html"])
	
    def test_remove_recipe_history_form_valid(self):
        RecipeHistoryEntry.objects.create(
              member = self.member,
              recipe=self.recipe,
              saving_date= date.today()
        )

        form_data = {
            "member": self.member.id,
            "recipe": self.recipe.id,
            "recipe_history_entry_date": date.today()
            }
        response = self.client.post(reverse("remove_recipe_history"), form_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json())
        self.assertTrue( response.json()["success"])
        self.assertIn("form_html", response.json())
        self.assertIn("recipe_history_entry_date", response.json()["form_html"])


        
        


		
		









