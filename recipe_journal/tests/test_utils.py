"""
Unit tests for the functions contained in the module utils.py.
"""
from django.contrib.auth.hashers import make_password
from django.test import RequestFactory, TestCase
import json
from recipe_journal.forms import RecipeCombinedForm, ManageRecipeCollectionForm
from recipe_journal.models import Ingredient, Member, Recipe
from recipe_journal.tests.test_config.mock_function_paths import MockFunctionPathManager
from recipe_journal.utils.utils import *
from recipe_journal.utils import utils
from django.urls import reverse
from unittest.mock import MagicMock, patch

path = MockFunctionPathManager()

MODEL_MAP = {
        "RecipeAlbumEntry": RecipeAlbumEntry,
        "RecipeToTryEntry": RecipeToTryEntry,
        "RecipeHistoryEntry": RecipeHistoryEntry
    }

class GetLoggedUserTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password"))
        self.member.save()

    def test_get_logged_user_valid(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        response  = self.client.get(reverse("welcome"))
        logged_user = get_logged_user(response.wsgi_request)
        self.assertIsNotNone(logged_user)
        self.assertEqual(logged_user.username, "testuser")
    
    def test_get_logged_user_no_user(self):
        response  = self.client.get(reverse("welcome"))
        logged_user = get_logged_user(response.wsgi_request)
        
        self.assertIsNone(logged_user)

class GetDailyRandomSampleTest(TestCase):
    def test_get_daily_random_sample_stable(self):
        Recipe.objects.create(title="Recipe 1")
        Recipe.objects.create(title="Recipe 2")
  
        result_1 = get_daily_random_sample(2)
        result_2 = get_daily_random_sample(2)
        
        self.assertEqual(result_1, result_2)

    def test_get_daily_random_sample_empty_database(self):
        result = get_daily_random_sample(5)
        
        self.assertEqual(result, [])

    def test_get_daily_random_sample_less_than_requested(self):
        Recipe.objects.create(title="Recipe 1")
        result = get_daily_random_sample(5)

        self.assertEqual(len(result), 1)

    def test_get_daily_random_sample_empty_list(self):
        result = get_daily_random_sample(2)

        self.assertEqual(result, [])

    def test_get_daily_random_sample_random_behavior(self):
        for ind in range(10):
            Recipe.objects.create(title=f"Recipe {ind}")
       
        result = get_daily_random_sample(2)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(id in range(1, 11) for id in result))

class ValidateTitleTest(TestCase):
    def test_validate_title_too_long(self):
        title = 30*"title trop long"
        self.assertIsNotNone(validate_title(title))
    
    def test_validate_title_valid(self):
        title = "recette test"
        self.assertIsNone(validate_title(title))

class GetRecipeIngredientListTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_recipe_ingredient_list_valid_data(self):
        form_data = {
            "name": ["carotte", "choux"],
            "quantity": [2, 1],
            "unit": ["kg", "u"]
            }
        expected_recipe_ingredient_list = [
            {"name": "carotte", "quantity": "2", "unit": "kg"},
            {"name": "choux", "quantity": "1", "unit": "u"},
        ]

        self.request = self.factory.post('/', form_data)
        recipe_ingredient_list = get_recipe_ingredient_list(self.request)
        self.assertEqual(recipe_ingredient_list, expected_recipe_ingredient_list)
    
    def test_get_recipe_ingredient_list_inconsistent_data(self):
        form_data = {
            "name": ["carotte", "choux"],
            "quantity": [2, 1],
            "unit": ["u"]
            }

        self.request = self.factory.post('/', form_data)
        recipe_ingredient_list = get_recipe_ingredient_list(self.request)
        self.assertEqual(recipe_ingredient_list, [])
    
    def test_get_recipe_ingredient_list_empty(self):
        form_data = {"name": [], "quantity": [], "unit": []}

        self.request = self.factory.post('/', form_data)
        recipe_ingredient_list = get_recipe_ingredient_list(self.request)
        self.assertEqual(recipe_ingredient_list, [])
    
    def test_get_recipe_ingredient_list_field_missing(self):
        form_data = {
            "name": ["carotte", "choux"],
            "unit": ["kg", "u"]
            }
        self.request = self.factory.post('/', form_data)
        recipe_ingredient_list = get_recipe_ingredient_list(self.request)
        self.assertEqual(recipe_ingredient_list, [])

class GetRecipeIngredientFormListTest(TestCase):
    def test_get_recipe_ingredient_form_valid_list(self):
        recipe_ingredient_list = [
            {"name": "carotte", "quantity": 2, "unit": "kg"},
            {"name": "choux", "quantity": 1, "unit": "u"},
        ]
        recipe_ingredient_form_list = get_recipe_ingredient_form_list(recipe_ingredient_list)

        self.assertEqual(len(recipe_ingredient_form_list), 2)

        for form, ingredient in zip(recipe_ingredient_form_list, recipe_ingredient_list):
            self.assertTrue(form.is_valid())
            self.assertEqual(form.cleaned_data['name'], ingredient['name'])
            self.assertEqual(form.cleaned_data['quantity'], ingredient['quantity'])
            self.assertEqual(form.cleaned_data['unit'], ingredient['unit'])
    
    def test_get_recipe_ingredient_form_empty_list(self):
        recipe_ingredient_list = []
        recipe_ingredient_form_list = get_recipe_ingredient_form_list(recipe_ingredient_list)

        self.assertEqual(len(recipe_ingredient_form_list), 1)
        self.assertFalse(recipe_ingredient_form_list[0].is_valid())

class InitializecombinedFormTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_initialize_combined_form_valid_data(self):
        form_data = {
            "title": "recette test",
            "category": "dessert",
            "cooking_time": 10,
            }
        self.request = self.factory.post('/', form_data)

        form = initialize_combined_form(RecipeCombinedForm, self.request)
        self.assertTrue(form.is_valid())
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data["main_form"]["title"], "recette test")
        self.assertEqual(cleaned_data["main_form"]["category"], "dessert")
        self.assertEqual(cleaned_data["secondary_form"]["cooking_time"], 10)

class InitializeFormTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_initialize_form_valid_data(self):
        self.request = self.factory.post("/", {"add_to_album": True})
        form = initialize_form(ManageRecipeCollectionForm, self.request)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["add_to_album"], True)

class CheckRequestValidityTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def check_status_code_400_message(self, params, expected_message):
        self.request = self.factory.get("/", params)
        logged_user, recipe_id, model, json_response = check_request_validity(self.request)
        self.assertIsNotNone(json_response)
        self.assertIsInstance(json_response, JsonResponse)

        response_data = json.loads(json_response.content)
        self.assertEqual(json_response.status_code, 400)
        self.assertIn("message", response_data)
        self.assertEqual(response_data["message"], expected_message)

    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_status_user_not_logged(self, mock_get_logged_user):
        mock_get_logged_user.return_value = None

        self.check_status_code_400_message(
            params=None,
            expected_message="Aucun utilisateur connecté."
            )
    
    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_no_recipe_id(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"

        self.check_status_code_400_message(
            params={"model_name": "mocked_model_name"},
            expected_message="ID de recette manquant."
            )

    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_no_model_name(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"

        self.check_status_code_400_message(
            params={"recipe_id": "mocked_recipe_id"},
            expected_message= "Modèle de collection manquant."
            )
    
    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_model_name_unvalid(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"
        params = {
            "recipe_id": "mocked_recipe_id",
            "model_name": "unvalid_model_name"
        }

        self.check_status_code_400_message(
            params=params,
            expected_message= f"Le modèle 'unvalid_model_name' est inconnu."
            )
    
    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_success(self, mock_get_logged_user):
        mock_get_logged_user.return_value =  "mocked_user"
        params = {
            "recipe_id": "mocked_repipe_id",
        }

        for model_name in MODEL_MAP:
            params["model_name"] = model_name
            self.request = self.factory.get("/", params)
            logged_user, recipe_id, model, json_response = check_request_validity(self.request)
            
            self.assertIsNone(json_response)
            self.assertEqual(logged_user, "mocked_user")
            self.assertEqual(recipe_id, "mocked_repipe_id")
            self.assertEqual(model, MODEL_MAP.get(model_name))

class ManageCollectionTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.recipe = Recipe.objects.create(title="recette test", category="plat")
        self.factory = RequestFactory()
    
    def _test_manage_collection(self, action, model, mocked_request_validity_json, expected_message, expected_status):
         with patch.object(utils, path.CHECK_REQUEST_VALIDITY) as mock_check_request_validity:
            mock_check_request_validity.return_value = self.member, self.recipe.id, model, mocked_request_validity_json
            self.request = self.factory.post("/")
            json_response = manage_collection(self.request, action=action)

            self.assertIsNotNone(json_response)
            self.assertIsInstance(json_response, JsonResponse)

            response_data = json.loads(json_response.content)

            self.assertEqual(json_response.status_code, expected_status)
            self.assertIn(expected_message, response_data["message"])

    def test_manage_collection_invalid_action(self):
        for model in MODEL_MAP.values():
            self._test_manage_collection(
                    action="invalid_action",
                    model=model,
                    mocked_request_validity_json=None,
                    expected_message="Une erreur est survenue: 'Action non valide'.",
                    expected_status=400
                )
    
    def test_manage_collection_error_response(self):
        mocked_request_validity_json = JsonResponse({"message": "Modèle de collection manquant."}, status=400)
        for action in ["add", "remove"]:
             for model in MODEL_MAP.values():
                self._test_manage_collection(
                    action=action,
                    model=model,
                    mocked_request_validity_json=mocked_request_validity_json,
                    expected_message="Modèle de collection manquant.",
                    expected_status=400
                )
    
    def test_manage_collection_add_recipe_success(self):
        for model in MODEL_MAP.values():
                self._test_manage_collection(
                    action="add",
                    model=model,
                    mocked_request_validity_json=None,
                    expected_message=f"La recette a été ajoutée à votre {model.title}.",
                    expected_status=200
                )

    def test_manage_collection_add_recipe_already_exists(self):
        for model in MODEL_MAP.values():
            model.objects.create(member=self.member, recipe_id=self.recipe.id)
            self._test_manage_collection(
                action="add",
                model=model,
                mocked_request_validity_json=None,
                expected_message=f"La recette fait déjà partie de votre {model.title}.",
                expected_status=200
                )

    def test_remove_from_collection(self):
        for model in MODEL_MAP.values():
            model.objects.create(member=self.member, recipe_id=self.recipe.id)
            self._test_manage_collection(
                action="remove",
                model=model,
                mocked_request_validity_json=None,
                expected_message=f"La recette a été supprimée de votre {model.title}.",
                expected_status=200
                )

    def test_remove_from_collection_not_exists(self):
        for model in MODEL_MAP.values():
            self._test_manage_collection(
                action="remove",
                model=model,
                mocked_request_validity_json=None,
                expected_message= f"La recette ne fait pas partie de votre {model.title}.",
                expected_status=200
                )
            
class PrepareRecipeFormsTest(TestCase):
    @patch.object(utils, path.INITIALIZE_FORM)
    @patch.object(utils, path.INITIALIZE_COMBINED_FORM)
    @patch.object(utils, path.GET_RECIPE_INGREDIENT_FORM_LIST)
    @patch.object(utils, path.GET_RECIPE_INGREDIENT_LIST)
    def test_prepare_recipe_forms(
        self,
        mock_get_recipe_ingredient_list,
        mock_get_recipe_ingredient_form_list,
        mock_initialize_combined_form,
        mock_initialize_form
        ):
        mock_get_recipe_ingredient_list.return_value = "mock_recipe_ingredient_list"
        mock_get_recipe_ingredient_form_list.return_value = "mock_recipe_ingredient_form_list"
        mock_initialize_combined_form.return_value = "mock_recipe_form"
        mock_initialize_form.return_value = "mock_recipe_action_form"
        self.factory = RequestFactory()
        self.request = self.factory.post("/")


        recipe_form, recipe_ingredient_form_list, recipe_action_form = prepare_recipe_forms(self.request)
        self.assertEqual((recipe_form, recipe_ingredient_form_list, recipe_action_form),
                         ("mock_recipe_form", "mock_recipe_ingredient_form_list", "mock_recipe_action_form"))
    
class AreFormsValidTest(TestCase):
    def setUp(self):
        self.mock_form_valid = MagicMock()
        self.mock_form_valid.is_valid.return_value = True
        self.mock_form_invalid = MagicMock()
        self.mock_form_invalid.is_valid.return_value = False

    def test_are_forms_valid_True(self):
        self.assertTrue(are_forms_valid(self.mock_form_valid, self.mock_form_valid))
    
    def test_are_forms_valid_False(self):
        self.assertFalse(are_forms_valid(self.mock_form_invalid, self.mock_form_valid))

    def test_are_forms_valid_False(self):
        self.assertFalse(are_forms_valid(self.mock_form_invalid, self.mock_form_invalid))



