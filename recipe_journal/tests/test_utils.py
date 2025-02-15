"""
Unit tests for the functions contained in the module utils.py.
"""
from django.contrib.auth.hashers import make_password
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
import json
from recipe_journal.forms import  FilterRecipeCollectionForm, AddRecipeToCollectionForm, RecipeCombinedForm
from recipe_journal.forms import RecipeIngredientForm, SearchRecipeForm
from recipe_journal.models import Ingredient, Member, Recipe, RecipeIngredient
from recipe_journal.tests.test_config.mock_function_paths import MockFunctionPathManager
from recipe_journal.utils.utils import *
from recipe_journal.utils import utils
from django.urls import reverse
from unittest.mock import MagicMock, patch

path = MockFunctionPathManager()

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

        request = self.factory.post('/', form_data)
        recipe_ingredient_list = get_recipe_ingredient_list(request)
        self.assertEqual(recipe_ingredient_list, [])
    
    def test_get_recipe_ingredient_list_empty(self):
        form_data = {"name": [], "quantity": [], "unit": []}

        request = self.factory.post('/', form_data)
        recipe_ingredient_list = get_recipe_ingredient_list(request)
        self.assertEqual(recipe_ingredient_list, [])
    
    def test_get_recipe_ingredient_list_field_missing(self):
        form_data = {
            "name": ["carotte", "choux"],
            "unit": ["kg", "u"]
            }
        request = self.factory.post('/', form_data)
        recipe_ingredient_list = get_recipe_ingredient_list(request)
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
        request = self.factory.post('/', form_data)

        form = initialize_combined_form(RecipeCombinedForm, request)
        self.assertTrue(form.is_valid())
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data["main_form"]["title"], "recette test")
        self.assertEqual(cleaned_data["main_form"]["category"], "dessert")
        self.assertEqual(cleaned_data["secondary_form"]["cooking_time"], 10)

class InitializeFormTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_initialize_form_valid_data(self):
        request = self.factory.post("/", {"add_to_album": True})
        form = initialize_form(AddRecipeToCollectionForm, request)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["add_to_album"], True)

class CheckRequestValidityTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def check_status_code_400_message(self, params, expected_message):
        request = self.factory.post("/", params)
        logged_user, recipe_id, collection_name, json_response = check_request_validity(request)
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
            params={"collection_name": "mocked_collection_name"},
            expected_message="ID de recette manquant."
            )

    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_no_collection_name(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"

        self.check_status_code_400_message(
            params={"recipe_id": "mocked_recipe_id"},
            expected_message= "Nom de la collection manquant."
            )
    
    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_collection_name_unvalid(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"
        params = {
            "recipe_id": "mocked_recipe_id",
            "collection_name": "unvalid_collection_name"
        }

        self.check_status_code_400_message(
            params=params,
            expected_message= f"Le modèle 'unvalid_collection_name' est inconnu."
            )
    
    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_success(self, mock_get_logged_user):
        mock_get_logged_user.return_value =  "mocked_user"
        params = {
            "recipe_id": "mocked_repipe_id",
        }

        for collection_name, _ in RecipeCollectionEntry.COLLECTION_CHOICES:
            params["collection_name"] = collection_name
            request = self.factory.post("/", params)
            logged_user, recipe_id, collection_name, json_response = check_request_validity(request)
            
            self.assertIsNone(json_response)
            self.assertEqual(logged_user, "mocked_user")
            self.assertEqual(recipe_id, "mocked_repipe_id")
            self.assertIn(collection_name, dict(RecipeCollectionEntry.COLLECTION_CHOICES).keys())

class UpdateCollectionTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.recipe = Recipe.objects.create(title="recette test", category="plat")
        self.factory = RequestFactory()

    
    def test_update_collection_collection_name_missing(self):
        mocked_request_validity_json = JsonResponse({"message": "Nom de la collection manquant."}, status=400)
        for action in ["add", "remove"]:
             for collection_name, _ in RecipeCollectionEntry.COLLECTION_CHOICES:
                self._test_update_collection(
                    action=action,
                    collection_name=collection_name,
                    mocked_request_validity_json=mocked_request_validity_json,
                    expected_message="Nom de la collection manquant.",
                    expected_status=400
                )
            
    def _test_update_collection(self, action, collection_name, mocked_request_validity_json, expected_message, expected_status):
        with patch.object(utils, path.CHECK_REQUEST_VALIDITY) as mock_check_request_validity:
            mock_check_request_validity.return_value = self.member, self.recipe.id, collection_name, mocked_request_validity_json
            
            request = self.factory.post("/")
            json_response = update_collection(request, action=action)

            self.assertIsNotNone(json_response)
            self.assertIsInstance(json_response, JsonResponse)

            response_data = json.loads(json_response.content)

            self.assertEqual(json_response.status_code, expected_status)
            self.assertIn(expected_message, response_data["message"])

    def test_update_collection_cases_1(self):
        for collection_name, collection_title in RecipeCollectionEntry.COLLECTION_CHOICES:
            params_list = [
                {
                    "action": "invalid_action",
                    "collection_name": collection_name,
                    "mocked_request_validity_json": None,
                    "expected_message": "Une erreur est survenue: 'Action non valide'.",
                    "expected_status": 400,
                },
                {
                    "action": "add",
                    "collection_name": collection_name,
                    "mocked_request_validity_json": None,
                    "expected_message": f"La recette a été ajoutée à votre {collection_title}.",
                    "expected_status": 200
                },
                {   
                    "action": "remove",
                    "collection_name": collection_name,
                    "mocked_request_validity_json": None,
                    "expected_message": f"La recette ne fait pas partie de votre {collection_title}.",
                    "expected_status": 200
                }
            ]

            for params in params_list:
                with self.subTest():
                    self._test_update_collection(**params)
                    RecipeCollectionEntry.objects.all().delete()

    def test_update_collection_cases_2(self):
        for collection_name, collection_title in RecipeCollectionEntry.COLLECTION_CHOICES:
            params_list = [
                {
                    "action": "add",
                    "collection_name": collection_name,
                    "mocked_request_validity_json": None,
                    "expected_message": f"La recette fait déjà partie de votre {collection_title}.",
                    "expected_status": 200,
                },
                {
                    "action": "remove",
                    "collection_name": collection_name,
                    "mocked_request_validity_json": None,
                    "expected_message": f"La recette a été supprimée de votre {collection_title}.",
                    "expected_status": 200
                }
            ]
            for params in params_list:
                with self.subTest():
                    RecipeCollectionEntry.objects.create(
                    collection_name=collection_name,
                    member=self.member,
                    recipe_id=self.recipe.id
                    )
                    self._test_update_collection(**params)
                    RecipeCollectionEntry.objects.all().delete()
                
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

class SaveRecipeAndIngredientsTest(TestCase):
    def setUp(self):
        recipe_form_data = {
            "title": "recette test",
            "category": "dessert"
        }
        recipe_ingredient_form_data = {
            "name": "ingredient test",
            "quantity": 2,
            "unit": "kg"
        }
        self.recipe_form = RecipeCombinedForm(recipe_form_data)
        self.recipe_ingredient_form_list = [RecipeIngredientForm(recipe_ingredient_form_data)]
        self.recipe_form.is_valid()
        self.recipe_ingredient_form_list[0].is_valid()
    
    def test_save_recipe_and_ingredients(self):
        recipe = save_recipe_and_ingredients(self.recipe_form, self.recipe_ingredient_form_list)
        self.assertIn(recipe, Recipe.objects.all())

class AddRecipeToCollectionIfCheckedTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.recipe = Recipe.objects.create(title="recette test", category="plat")

    def _test_add_recipe_to_collection_if_checked(self, add_recipe_to_collection_form_data):
        add_recipe_to_collection_form = AddRecipeToCollectionForm(add_recipe_to_collection_form_data)
        add_recipe_to_collection_form.is_valid()
        
        for collection_name, action in AddRecipeToCollectionForm.COLLECTION_NAME_MAPPING.items():
            added = add_recipe_to_collection_if_checked(
                        add_recipe_to_collection_form,
                        collection_name,
                        self.member,
                        self.recipe
                    )
            recipe_collection_exist = RecipeCollectionEntry.objects.filter(
                    collection_name=collection_name,
                    member=self.member,
                    recipe=self.recipe
                    ).exists()
            self.assertEqual(added, recipe_collection_exist)

    def test_add_recipe_to_collection_if_checked_case1(self):
        add_recipe_to_collection_form = {"add_to_history": True}
        self._test_add_recipe_to_collection_if_checked(add_recipe_to_collection_form)
    
    def test_add_recipe_to_collection_if_checked_case2(self):
        add_recipe_to_collection_form = {
            "add_to_history": True,
            "add_to_album": True
            }
        self._test_add_recipe_to_collection_if_checked(add_recipe_to_collection_form)
    
    def test_add_recipe_to_collection_if_checked_case3(self):
        add_recipe_to_collection_form = {
            }
        self._test_add_recipe_to_collection_if_checked(add_recipe_to_collection_form)
    
    def test_add_recipe_to_collection_if_checked_case4(self):
        add_recipe_to_collection_form = {
            "add_to_history": True,
            "add_to_album": True,
            "add_to_recipe_to_try": True,
            }
        self._test_add_recipe_to_collection_if_checked(add_recipe_to_collection_form)

class LinkRecipeToCollectionsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.post("/")
        setattr(self.request, "session", {})
        setattr(self.request, "_messages", FallbackStorage(self.request))
    
    def mock_add_recipe_to_album(self, add_recipe_to_collection_form, model_name, logged_user, recipe):
        if model_name == "album":
            return True
        return False
    
    @patch.object(utils, path.ADD_RECIPE_TO_COLLECTION_IF_CHECKED)
    def test_handle_recipe_collections_add_to_album(self, mock_add_recipe_to_collection_if_checked):
        mock_add_recipe_to_collection_if_checked.side_effect = self.mock_add_recipe_to_album
        mock_add_recipe_to_collection_form = "mock_add_recipe_to_collection_form"
        mock_logged_user = "mock_logged_user"
        mock_recipe = "mock_recipe"
        link_recipe_to_collections(
            mock_add_recipe_to_collection_form,
            mock_logged_user,
            mock_recipe,
            self.request
            )

        messages_list = list(get_messages(self.request))
        self.assertEqual(len(messages_list), 1)
        collection_title = dict(RecipeCollectionEntry.COLLECTION_CHOICES).get("album")
        self.assertTrue(
            f"Recette ajoutée à votre {collection_title}" in messages_list[0].message
            )

    @patch.object(utils, path.ADD_RECIPE_TO_COLLECTION_IF_CHECKED)
    def test_handle_recipe_collections_add_to_all_collection(self, mock_add_recipe_to_collection_if_checked):
        mock_add_recipe_to_collection_if_checked.return_value = True
        mock_add_recipe_to_collection_form = "mock_add_recipe_to_collection_form"
        mock_logged_user = "mock_logged_user"
        mock_recipe = "mock_recipe"
        link_recipe_to_collections(
            mock_add_recipe_to_collection_form,
            mock_logged_user,
            mock_recipe,
            self.request
            )

        messages_list = list(get_messages(self.request))
        self.assertEqual(len(messages_list), len(RecipeCollectionEntry.COLLECTION_CHOICES))
        for _, collection_title in RecipeCollectionEntry.COLLECTION_CHOICES:
            self.assertTrue(any(f"Recette ajoutée à votre {collection_title}" in message.message for message in messages_list))
    
    @patch.object(utils, path.ADD_RECIPE_TO_COLLECTION_IF_CHECKED)
    def test_handle_recipe_collections_no_add(self, mock_add_recipe_to_collection_if_checked):
        mock_add_recipe_to_collection_if_checked.return_value = False
        mock_add_recipe_to_collection_form = "mock_add_recipe_to_collection_form"
        mock_logged_user = "mock_logged_user"
        mock_recipe = "mock_recipe"
        link_recipe_to_collections(
            mock_add_recipe_to_collection_form,
            mock_logged_user,
            mock_recipe,
            self.request
            )

        self.assertEqual(len(get_messages(self.request)), 0)

class HandleAddFriendRequestTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.friend  = Member.objects.create(username="test_friend", password="password")
        self.factory = RequestFactory()
        
    def test_handle_add_friend_request_form_invalid(self):
        self.request = self.factory.post("/")
        setattr(self.request, "session", {})
        setattr(self.request, "_messages", FallbackStorage(self.request))
        form = handle_add_friend_request(self.request, self.member)
        
        self.assertEqual(len(get_messages(self.request)), 0)
        self.assertFalse(form.is_valid())
        self.assertIn("username_to_add", form.fields)
    
    def test_handle_add_friend_request_form_valid(self):
        self.request = self.factory.post("/", {"username_to_add": "test_friend"})
        setattr(self.request, "session", {})
        setattr(self.request, "_messages", FallbackStorage(self.request))
        form = handle_add_friend_request(self.request, self.member)
        messages_list = list(get_messages(self.request))

        self.assertTrue(form.is_valid())
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(f"Nous avons ajouté test_friend à votre liste d'amis !", messages_list[0].message)
        self.assertIn(self.friend, self.member.friends.all())
    
class HandleRemoveFriendRequestTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.friend  = Member.objects.create(username="test_friend", password="password")
        self.factory = RequestFactory()
    
    def test_handle_remove_friend_request_username_to_remove_empty(self):
        self.request = self.factory.post("/", {"username_to_remove": ""})
        setattr(self.request, "session", {})
        setattr(self.request, "_messages", FallbackStorage(self.request))
        handle_remove_friend_request(self.request, self.member)
        messages_list = list(get_messages(self.request))

        self.assertEqual(len(messages_list), 1)
        self.assertEqual("Aucun utilisateur à supprimer.", messages_list[0].message)
    
    def test_handle_remove_friend_request_success(self):
        self.member.friends.add(self.friend)
        self.request = self.factory.post("/", {"username_to_remove": "test_friend"})
        setattr(self.request, "session", {})
        setattr(self.request, "_messages", FallbackStorage(self.request))

        self.assertIn(self.friend, self.member.friends.all())
        
        handle_remove_friend_request(self.request, self.member)
        messages_list = list(get_messages(self.request))

        self.assertEqual(len(messages_list), 1)
        self.assertEqual("L'utilisateur test_friend a été retiré de votre liste d'amis.", messages_list[0].message)
        self.assertNotIn(self.friend, self.member.friends.all())
    
    def test_handle_remove_friend_request_friend_not_valid(self):
        self.request = self.factory.post("/", {"username_to_remove": "test_friend"})
        setattr(self.request, "session", {})
        setattr(self.request, "_messages", FallbackStorage(self.request))       
        handle_remove_friend_request(self.request, self.member)
        messages_list = list(get_messages(self.request))

        self.assertEqual(len(messages_list), 1)
        self.assertEqual("L'utilisateur test_friend ne fait pas partie de votre liste d'amis.", messages_list[0].message)
        self.assertNotIn(self.friend, self.member.friends.all())

class NormalizeIngredienTest(TestCase):
    def test_normalize_ingredient_not_None(self):
        self.assertEqual(normalize_ingredient("pommes de terre"), "pomme de terre")
    
    def test_normalize_ingredient_None(self):
        ingredient_name = None
        result = normalize_ingredient(ingredient_name)

        self.assertIsNone(result)

class GetIngredientInputsTest(TestCase):
    @patch.object(utils, path.NORMALIZE_INGREDIENT)
    def test_get_ingredient_inputs(self, mock_normalize_ingredient):
        form_data = {
            "ingredient_1": "carottes",
            "ingredient_2": "poireaux",
            "ingredient_3": "pommes de terre",
        }
        side_effect = ("carotte", "poireau", "pomme de terre")
        form = SearchRecipeForm(form_data)
        form.is_valid()
        mock_normalize_ingredient.side_effect = side_effect
        ingredient_inputs_dict = get_ingredient_inputs(form)

        self.assertEqual(mock_normalize_ingredient.call_count, 3)

        self.assertEqual(set(ingredient_inputs_dict.items()), set(zip(form_data.keys(), side_effect)))

class FilterCollectionByMemberTest(TestCase):
    def setUp(self):
        self.logged_user = Member.objects.create(username="test_user", password="password")
        for recipe_title in ["recette logged user", "recette commune"]:
            recipe = Recipe.objects.create(title= recipe_title, category="plat")
            RecipeCollectionEntry.objects.create(collection_name="album", member=self.logged_user, recipe=recipe)
        self.generic_expected_recipe_title_list = ["recette commune"]
        self.shared_recipe = Recipe.objects.get(title="recette commune")
        
        for ind in range(1, 3):
            friend  = Member.objects.create(username=f"test_friend{ind}", password="password")
            recipe = Recipe.objects.create(title=f"recette friend{ind}", category="plat")
            for model_name in ["album", "history"]:
                RecipeCollectionEntry.objects.create(collection_name=model_name, member=friend, recipe=recipe)
                RecipeCollectionEntry.objects.create(collection_name=model_name, member=friend, recipe=self.shared_recipe)
            self.logged_user.friends.add(friend)
            self.generic_expected_recipe_title_list.append(f"recette friend{ind}")
    
    def _test_filter_collection_by_member(self, member, expected_qs_length, recipe_title_to_add):
        recipe_qs = filter_collection_by_member(
            logged_user=self.logged_user,
            member=member,
            recipe_collection_qs=RecipeCollectionEntry.objects.filter(collection_name__in=["album", "history"])
            )
        self.assertEqual(len(recipe_qs), expected_qs_length)
        expected_recipe_title_list = self.generic_expected_recipe_title_list.copy()
        if recipe_title_to_add:
             expected_recipe_title_list.append(recipe_title_to_add)
        self.assertEqual(len(recipe_qs.filter(title__in=expected_recipe_title_list)), expected_qs_length)
    
    def test_filter_collection_by_member_equal_friends(self):
        self._test_filter_collection_by_member(member="friends", expected_qs_length=3, recipe_title_to_add=None)
    
    def test_filter_by_member_equal_empty(self):
        self._test_filter_collection_by_member(member="", expected_qs_length=4, recipe_title_to_add="recette logged user")

class HandleSearchRecipeRequestTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        ingredient = Ingredient.objects.create(name="carotte")
        recipe_ingredient = RecipeIngredient.objects.create(ingredient=ingredient, quantity=1, unit="u")
        for ind in range(1, 3):
            Recipe.objects.create(title=f"recette plat_{ind}", category="plat")
            Recipe.objects.create(title=f"recette dessert_{ind}", category="plat")
        Recipe.objects.get(title=f"recette plat_{1}", category="plat").recipe_ingredient.add(recipe_ingredient)
        self.factory = RequestFactory()


    def test_handle_search_form_not_valid(self):        
        self.request = self.factory.get("/", {"category": "unvalid_category"})
        form, recipe_qs = handle_search_recipe_request(self.request, self.member)
        
        self.assertEqual(len(recipe_qs.all()), 4)
        self.assertIsInstance(form, SearchRecipeForm)
        self.assertIn("category", form.errors)
    
    @patch.object(utils, path.FILTER_COLLECTION_BY_MEMBER)
    @patch.object(utils, path.GET_INGREDIENT_INPUTS)
    def test_handle_search_form_cases(self, mock_get_ingredient_inputs, mock_filter_collection_by_member):
        for (ingredient_1, title) in [("carotte", ""), ("", "recette plat_1")]:
            with self.subTest():
                mock_ingredient_imputs_dict = {"ingredient_1": ingredient_1}
                mock_get_ingredient_inputs.return_value = mock_ingredient_imputs_dict
                mock_filter_collection_by_member.return_value = Recipe.objects.all()
                
                request = self.factory.get("/", {"title": title, "ingredient_1": ingredient_1})
                form, recipe_qs = handle_search_recipe_request(request, self.member)
                
                self.assertTrue(form.is_valid())
                
                filter_data = dict()
                if ingredient_1 != "":
                    filter_data["recipe_ingredient__ingredient__name"] = ingredient_1
                if title != "":
                    filter_data["title"] = title
                expected_qs = Recipe.objects.filter(**filter_data)

                self.assertCountEqual(recipe_qs, expected_qs)
                self.assertIsInstance(form, SearchRecipeForm)
                print(f"\n Tested", ingredient_1, title)

class GetMemberRecipeCollectionEntriesTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.recipe1 = Recipe.objects.create(title="Recette 1", category="plat")
        self.recipe2 = Recipe.objects.create(title="Recette 2", category="plat")

        for collection_name, _ in RecipeCollectionEntry.COLLECTION_CHOICES:
            RecipeCollectionEntry.objects.create(
                collection_name=collection_name,
                member=self.member,
                recipe=self.recipe1,
                saving_date="2025-02-01"
            )
            RecipeCollectionEntry.objects.create(
                collection_name=collection_name,
                member=self.member,
                recipe=self.recipe2,
                saving_date="2025-02-02"
            )


    def test_get_member_recipe_collection_entries_with_recipe_history(self):
        entries = get_member_recipe_collection_entries("history", self.member)
        expected_entries_list = [
            RecipeCollectionEntry.objects.get(collection_name="history", saving_date="2025-02-02"),
            RecipeCollectionEntry.objects.get(collection_name="history", saving_date="2025-02-01")
        ]
        self.assertEqual(list(entries), expected_entries_list)

    def test_get_member_recipe_collection_entries_with_other_model(self):
        for collection_name in ["album", "trials"]:
            expected_entries_list = [
                RecipeCollectionEntry.objects.get(collection_name=collection_name, recipe__title="Recette 1"),
                RecipeCollectionEntry.objects.get(collection_name=collection_name, recipe__title="Recette 2")
            ]
            with self.subTest():
                entries = get_member_recipe_collection_entries(collection_name, self.member)
                self.assertEqual(list(entries), expected_entries_list)
                print(f"\nTested {collection_name}")

class FilterMemberRecipeCollection(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        ingredient = Ingredient.objects.create(name="carotte")
        recipe_ingredient = RecipeIngredient.objects.create(ingredient=ingredient, quantity=1, unit="u")
        self.recipe1 = Recipe.objects.create(title="Recette 1", category="plat")
        self.recipe2 = Recipe.objects.create(title="Recette 2", category="plat")
        self.recipe3 = Recipe.objects.create(title="Recette 3", category="dessert")
        self.recipe2.recipe_ingredient.add(recipe_ingredient)
        self.recipe3.recipe_ingredient.add(recipe_ingredient)

        for collection_name, _ in RecipeCollectionEntry.COLLECTION_CHOICES:
            RecipeCollectionEntry.objects.create(
                collection_name=collection_name,
                member=self.member,
                recipe=self.recipe1,
                saving_date="2025-02-01"
            )
            RecipeCollectionEntry.objects.create(
                collection_name=collection_name,
                member=self.member,
                recipe=self.recipe2,
                saving_date="2025-02-02"
            )
        self.factory = RequestFactory()
        
    def test_filter_member_recipe_collection_form_invalid(self):
        form_data = {}
        request = self.factory.post("/", form_data)
        form, recipe_collection_entries = filter_member_recipe_collection(request)

        self.assertEqual(recipe_collection_entries.count(), 0)
        self.assertIsInstance(form, FilterRecipeCollectionForm)
        self.assertFalse(form.is_valid())
        self.assertIn("member", form.errors)
        self.assertIn("This field is required", form.errors["member"][0])
        self.assertIn("collection_name", form.errors)
        self.assertIn("This field is required", form.errors["collection_name"][0])
    
    def _test_filter_member_recipe_collection(self, partial_form_data, collection_name):
        with patch.object(utils, path.GET_INGREDIENT_INPUTS) as mock_ingredient_inputs, \
        patch.object(utils, path.GET_MEMBER_RECIPE_COLLECTION_ENTRIES) as mock_get_member_recipe_collection_entries:
            mock_ingredient_inputs.return_value = {"ingredient_1": "carotte"}
            mock_get_member_recipe_collection_entries.return_values = RecipeCollectionEntry.objects.filter(
                collection_name=collection_name,
                member=self.member
                )
            
            form_data = partial_form_data.copy()
            form_data["member"] = self.member
            form_data["collection_name"] = collection_name
            request = self.factory.post("/", form_data)
            form, recipe_collection_entries = filter_member_recipe_collection(request)

            filter_data = {
                f"recipe__{key}" if "ingredient" not in key else "recipe__recipe_ingredient__ingredient__name": value
                for key, value in partial_form_data.items()
            }
            expected_recipe_collection_entries = RecipeCollectionEntry.objects.filter(collection_name=collection_name, **filter_data)

            self.assertIsInstance(form, FilterRecipeCollectionForm)
            self.assertFalse(form.is_valid())
            self.assertEqual(recipe_collection_entries.count(), expected_recipe_collection_entries.count())
    
    def test_filter_member_recipe_collection_cases(self):
        for i, partial_form_data in enumerate([
            {"category": "dessert"},
            {
                "category": "dessert",
                "title": "Recette 2"
             },
             {
                "category": "dessert",
                "title": "Recette 2",
                "ingredient_1": "carottes"
             },
            ]):
            for collection_name, _ in RecipeCollectionEntry.COLLECTION_CHOICES:
                with self.subTest():
                    print(f"\nTested partial_form{i}, {collection_name}")
                    self._test_filter_member_recipe_collection(partial_form_data, collection_name)
                    print(f"\nTested partial_form{i}, {collection_name}")






