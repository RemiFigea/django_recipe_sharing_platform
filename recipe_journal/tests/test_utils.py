"""Unit tests for the utils module."""

from datetime import date, timedelta
from django.contrib.auth.hashers import make_password
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import transaction
from django.test import RequestFactory, TestCase
from django.urls import reverse
import json
from recipe_journal.forms import  AddRecipeToCollectionsForm, RecipeCombinedForm, ShowRecipeCollectionForm
from recipe_journal.forms import RecipeIngredientForm, SearchRecipeForm
from recipe_journal.models import Ingredient, Member, Recipe, RecipeIngredient
from recipe_journal.tests.test_config.mock_function_paths import MockFunctionPathManager
from recipe_journal.utils import utils
from recipe_journal.utils.utils import *
from unittest.mock import MagicMock, patch

path = MockFunctionPathManager()

class GetLoggedUserTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password"))
        self.member.save()

    def test_get_logged_with_valid_login_data(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        response  = self.client.get(reverse("welcome"))
        logged_user = get_logged_user(response.wsgi_request)

        self.assertIsNotNone(logged_user)
        self.assertEqual(logged_user.username, "testuser")
    
    def test_get_logged_without_login_data(self):
        response  = self.client.get(reverse("welcome"))
        logged_user = get_logged_user(response.wsgi_request)
        
        self.assertIsNone(logged_user)

class GetDailyRandomSampleTest(TestCase):
    def test_get_daily_random_sample_is_stable(self):
        Recipe.objects.create(title="Recipe 1")
        Recipe.objects.create(title="Recipe 2")
  
        result_1 = get_daily_random_sample(2)
        result_2 = get_daily_random_sample(2)
        
        self.assertEqual(result_1, result_2)

    def test_get_daily_random_sample_empty_database(self):
        result = get_daily_random_sample(5)
        
        self.assertEqual(result, [])

    def test_get_daily_random_sample_less_recipes_than_requested(self):
        Recipe.objects.create(title="Recipe 1")
        result = get_daily_random_sample(5)

        self.assertEqual(len(result), 1)

    def test_get_daily_random_sample_randomness(self):
        for ind in range(10):
            Recipe.objects.create(title=f"Recipe {ind}")
       
        result = get_daily_random_sample(2)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(id in range(1, 11) for id in result))

class GetTopAndThumbnailRecipesTest(TestCase):
    def setUp(self):
        for ind in range(1, 11):
            Recipe.objects.create(title=f"recette {ind}", category="dessert")
    
    def test_get_top_and_thumbnail_recipes_recipe_ids_list_longer_than_top_recipe_nb(self):
        recipe_ids_list = list(range(1, 7))
        top_recipe_nb = 2
        top_recipe_qs, thumbnail_recipe_qs = get_top_and_thumbnail_recipes(recipe_ids_list, top_recipe_nb)

        self.assertEqual(top_recipe_qs.count(), 2)
        self.assertEqual(set(top_recipe_qs), set(Recipe.objects.filter(id__in=recipe_ids_list[:2])))
        self.assertEqual(thumbnail_recipe_qs.count(), 4)
        self.assertEqual(set(thumbnail_recipe_qs), set(Recipe.objects.filter(id__in=recipe_ids_list[2:])))
    
    def test_get_top_and_thumbnail_recipes_recipe_ids_list_shorter_than_top_recipe_nb(self):
        recipe_ids_list = list(range(1, 7))
        top_recipe_nb = 10
        top_recipe_qs, thumbnail_recipe_qs = get_top_and_thumbnail_recipes(recipe_ids_list, top_recipe_nb)

        self.assertEqual(top_recipe_qs.count(), 6)
        self.assertEqual(set(top_recipe_qs), set(Recipe.objects.filter(id__in=recipe_ids_list)))
        self.assertEqual(thumbnail_recipe_qs.count(), 0)

    def test_get_top_and_thumbnail_recipes_recipe_ids_list_empty(self):
        recipe_ids_list = []
        top_recipe_nb = 10
        top_recipe_qs, thumbnail_recipe_qs = get_top_and_thumbnail_recipes(recipe_ids_list, top_recipe_nb)

        self.assertEqual(top_recipe_qs.count(), 0)
        self.assertEqual(thumbnail_recipe_qs.count(), 0)
    
    def test_get_top_and_thumbnail_recipes_top_recipe_nb_zero(self):
        recipe_ids_list = list(range(1, 7))
        top_recipe_nb = 0
        top_recipe_qs, thumbnail_recipe_qs = get_top_and_thumbnail_recipes(recipe_ids_list, top_recipe_nb)

        self.assertEqual(top_recipe_qs.count(), 0)
        self.assertEqual(thumbnail_recipe_qs.count(), 6)
        self.assertEqual(set(thumbnail_recipe_qs), set(Recipe.objects.filter(id__in=recipe_ids_list)))
    
    def test_get_top_and_thumbnail_recipes_recipe_ids_list_longer_than_existing_recipes(self):
        recipe_ids_list = list(range(1, 15))
        top_recipe_nb = 2
        top_recipe_qs, thumbnail_recipe_qs = get_top_and_thumbnail_recipes(recipe_ids_list, top_recipe_nb)

        self.assertEqual(top_recipe_qs.count(), 2)
        self.assertEqual(set(top_recipe_qs), set(Recipe.objects.filter(id__in=recipe_ids_list[:2])))
        self.assertEqual(thumbnail_recipe_qs.count(), 8)
        self.assertEqual(set(thumbnail_recipe_qs), set(Recipe.objects.filter(id__in=recipe_ids_list[2:])))

class ValidateTitleTest(TestCase):
    def test_validate_title_title_too_long(self):
        title = 30*"title trop long"

        self.assertIsNotNone(validate_title(title))
    
    def test_validate_title_valid_title(self):
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
    
    def _test_get_recipe_ingredient_list(self, form_data):
        request = self.factory.post('/', form_data)
        recipe_ingredient_list = get_recipe_ingredient_list(request)
        
        self.assertEqual(recipe_ingredient_list, [])

    def test_get_recipe_ingredient_list_return_empty_list(self):
        test_cases = [
            {
                "desc": "inconsistant form_data",
                "form_data": {
                    "name": ["carotte", "choux"],
                    "quantity": [2, 1],
                    "unit": ["u"]
                }
            },
            {
                "desc": "empty field",
                "form_data": {
                    "name": [],
                    "quantity": [],
                    "unit": []
                }
            },
            {
                "desc": "missing field 'name'",
                "form_data": {
                    "name": ["carotte", "choux"],
                    "unit": ["kg", "u"]
                }
            }
        ]
        for case in test_cases:
            with self.subTest(msg=case["desc"]):
                self._test_get_recipe_ingredient_list(case["form_data"])

class GetRecipeIngredientFormListTest(TestCase):
    def test_get_recipe_ingredient_form_valid_data(self):
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
        form = initialize_form(AddRecipeToCollectionsForm, request)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["add_to_album"], True)
         
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
   
    def test_are_forms_valid(self):
        self.assertTrue(are_forms_valid(self.mock_form_valid, self.mock_form_valid))
        self.assertFalse(are_forms_valid(self.mock_form_invalid, self.mock_form_valid))
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

class CreateRecipeCollectionEntryTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.recipe = Recipe.objects.create(title="recette test", category="plat")

    def _test_create_recipe_collection_entry(self, add_recipe_to_collection_form_data):
        add_recipe_to_collection_form = AddRecipeToCollectionsForm(add_recipe_to_collection_form_data)
        add_recipe_to_collection_form.is_valid()
        
        for collection_name in AddRecipeToCollectionsForm.COLLECTION_NAME_MAPPING:
            added = create_recipe_collection_entry(
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

    def test_create_recipe_collection_entry_cases(self):
        test_cases = [
            {
                "desc": "add to history",
                "form_data": {"add_to_history": True}
            },
            {
                "desc": "add to history and album",
                "form_data": {"add_to_history": True, "add_to_album": True}
            },
            {
                "desc": "form_data empty",
                "form_data": {}
            },
            {
                "desc": "add to history, album and trials",
                "form_data": {"add_to_history": True, "add_to_album": True, "add_to_trials": True}
            }
        ]
        for case in test_cases:
            with self.subTest(msg=case["desc"]):
                with transaction.atomic():
                    self._test_create_recipe_collection_entry(case["form_data"])
                    transaction.set_rollback(True)

class AddRecipeToCollectionsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.post("/")
        setattr(self.request, "session", {})
        setattr(self.request, "_messages", FallbackStorage(self.request))
    
    def mock_add_recipe_to_album(self, add_recipe_to_collection_form, collection_name, logged_user, recipe):
        if collection_name == "album":
            return True
        return False
    
    @patch.object(utils, path.CREATE_RECIPE_COLLECTION_ENTRY)
    def test_add_recipe_to_collections_add_to_album(self, mock_create_recipe_collection_entry):
        mock_create_recipe_collection_entry.side_effect = self.mock_add_recipe_to_album
        mock_add_recipe_to_collection_form = "mock_add_recipe_to_collection_form"
        mock_logged_user = "mock_logged_user"
        mock_recipe = "mock_recipe"
        
        add_recipe_to_collections(
            mock_add_recipe_to_collection_form,
            mock_logged_user,
            mock_recipe,
            self.request
            )
        messages_list = list(get_messages(self.request))
        
        self.assertEqual(len(messages_list), 1)
        
        collection_title = dict(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES).get("album")
        
        self.assertTrue(
            f"Recette ajoutée à votre {collection_title}" in messages_list[0].message
            )

    @patch.object(utils, path.CREATE_RECIPE_COLLECTION_ENTRY)
    def test_add_recipe_to_collections_add_to_all_collections(self, mock_create_recipe_collection_entry):
        mock_create_recipe_collection_entry.return_value = True
        mock_add_recipe_to_collection_form = "mock_add_recipe_to_collection_form"
        mock_logged_user = "mock_logged_user"
        mock_recipe = "mock_recipe"
        add_recipe_to_collections(
            mock_add_recipe_to_collection_form,
            mock_logged_user,
            mock_recipe,
            self.request
            )
        messages_list = list(get_messages(self.request))
        
        self.assertEqual(len(messages_list), len(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES))
        
        for _, collection_title in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES:
            self.assertTrue(any(f"Recette ajoutée à votre {collection_title}" in message.message for message in messages_list))
    
    @patch.object(utils, path.CREATE_RECIPE_COLLECTION_ENTRY)
    def test_add_recipe_to_collections_dont_add_to_any_collection(self, mock_create_recipe_collection_entry):
        mock_create_recipe_collection_entry.return_value = False
        mock_add_recipe_to_collection_form = "mock_add_recipe_to_collection_form"
        mock_logged_user = "mock_logged_user"
        mock_recipe = "mock_recipe"
        add_recipe_to_collections(
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
        
    def test_handle_add_friend_request_empty_form(self):
        request = self.factory.post("/")
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))
        form = handle_add_friend_request(request, self.member)
        
        self.assertEqual(len(get_messages(request)), 0)
        self.assertFalse(form.is_valid())
        self.assertIn("username_to_add", form.fields)
    
    def test_handle_add_friend_request_valid_form(self):
        request = self.factory.post("/", {"username_to_add": "test_friend"})
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))
        form = handle_add_friend_request(request, self.member)
        messages_list = list(get_messages(request))

        self.assertTrue(form.is_valid())
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(f"Nous avons ajouté test_friend à votre liste d'amis !", messages_list[0].message)
        self.assertIn(self.friend, self.member.friends.all())
    
class HandleRemoveFriendRequestTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.friend  = Member.objects.create(username="test_friend", password="password")
        self.factory = RequestFactory()
    
    def test_handle_remove_friend_request_empty_username_to_remove(self):
        request = self.factory.post("/", {"username_to_remove": ""})
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))
        handle_remove_friend_request(request, self.member)
        messages_list = list(get_messages(request))

        self.assertEqual(len(messages_list), 1)
        self.assertEqual("Aucun utilisateur à supprimer.", messages_list[0].message)
    
    def test_handle_remove_friend_request_valid_username_to_remove(self):
        self.member.friends.add(self.friend)
        request = self.factory.post("/", {"username_to_remove": "test_friend"})
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))

        self.assertIn(self.friend, self.member.friends.all())
        
        handle_remove_friend_request(request, self.member)
        messages_list = list(get_messages(request))

        self.assertEqual(len(messages_list), 1)
        self.assertEqual("L'utilisateur test_friend a été retiré de votre liste d'amis.", messages_list[0].message)
        self.assertNotIn(self.friend, self.member.friends.all())
    
    def test_handle_remove_friend_request_username_to_remove_not_in_friends(self):
        request = self.factory.post("/", {"username_to_remove": "test_friend"})
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))       
        handle_remove_friend_request(request, self.member)
        messages_list = list(get_messages(request))

        self.assertEqual(len(messages_list), 1)
        self.assertEqual("L'utilisateur test_friend ne fait pas partie de votre liste d'amis.", messages_list[0].message)
        self.assertNotIn(self.friend, self.member.friends.all())

class NormalizeIngredienTest(TestCase):
    def test_normalize_ingredient_valid_name(self):
        self.assertEqual(normalize_ingredient("pommes de terre"), "pomme de terre")
    
    def test_normalize_ingredient_name_is_none(self):
        ingredient_name = None
        result = normalize_ingredient(ingredient_name)

        self.assertIsNone(result)

class GetIngredientInputsTest(TestCase):
    @patch.object(utils, path.NORMALIZE_INGREDIENT)
    def test_get_ingredient_inputs_valid_form(self, mock_normalize_ingredient):
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

class GetRecipeCollectionBySortOrderTest(TestCase):
    def setUp(self):
        member = Member.objects.create(username="test user", password="password")
        for ind in range(1, 5):
            recipe = Recipe.objects.create(title=f"recette test {ind}", category="dessert")
            for collection_name, _ in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES:
                RecipeCollectionEntry.objects.create(
                    collection_name=collection_name,
                    member=member,
                    recipe=recipe,
                    saving_date=date.today()+timedelta(days=ind)
                    )
                
    def test_get_recipe_collection_by_sort_order_history(self):
        recipe_collection_qs = get_recipe_collection_by_sort_order("history")
        expected_recipe_ids_order = list(range(1, 5))[::-1]
        
        self.assertEqual(
            list(recipe_collection_qs.values_list("recipe__id", flat=True)),
            expected_recipe_ids_order
            )
    
    def test_get_recipe_collection_by_sort_order_non_history(self):
        for collection_name, _ in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES:
            if collection_name!="history":
                with self.subTest():
                    recipe_collection_qs = get_recipe_collection_by_sort_order(collection_name)
                    expected_recipe_ids_order = list(range(1, 5))
                    
                    self.assertEqual(
                        list(recipe_collection_qs.values_list("recipe__id", flat=True)),
                        expected_recipe_ids_order
                        )

class FilterRecipeCollectionByMemberTest(TestCase):
    def setUp(self):
        self.logged_user = Member.objects.create(username="test_user", password="password")
        for ind in range(1, 3):
            recipe = Recipe.objects.create(title=f"recette_{ind}", category="plat")
            RecipeCollectionEntry.objects.create(collection_name="album", member=self.logged_user, recipe=recipe)
        
        self.friend_1  = Member.objects.create(username=f"friend_1", password="password")
        self.friend_2 = Member.objects.create(username=f"friend_2", password="password")
        for ind_recette in range(11, 13):
            recipe = Recipe.objects.create(title=f"recette_{ind_recette}", category="plat")
            for friend in [self.friend_1, self.friend_2]:
                self.logged_user.friends.add(friend)
                RecipeCollectionEntry.objects.create(collection_name="album", member=friend, recipe=recipe)
        
        self.initial_recipe_collection_qs = RecipeCollectionEntry.objects.all()
    
    def test_filter_recipe_collection_by_member_raises_exception_when_friends_and_no_logged_user(self):
        params = {"member": "friends", "logged_user": None}
        with self.assertRaises(ValueError) as context:
            filter_recipe_collection_by_member(self.initial_recipe_collection_qs, **params)
       
        self.assertEqual(str(context.exception), "logged_user doit être défini si member == 'friends'")

    
    def _test_filter_recipe_collection_by_member(
            self,
            params,
            expected_recipe_collection_qs):
        recipe_collection_qs = filter_recipe_collection_by_member(self.initial_recipe_collection_qs, **params)
        
        self.assertEqual(list(recipe_collection_qs), list(expected_recipe_collection_qs))
    
    def test_filter_recipe_collection_by_member_cases_return_all(self):
        params = {
            "member": None,
            "logged_user": self.logged_user
            }

        self._test_filter_recipe_collection_by_member(params, self.initial_recipe_collection_qs)

    def test_filter_recipe_collection_by_member_with_member_friends_and_logged_user(self):
        params = {"member": "friends", "logged_user": self.logged_user}
        expected_recipe_collection_qs = self.initial_recipe_collection_qs.filter(member__username__in=["friend_1", "friend_2"])

        self._test_filter_recipe_collection_by_member(params, expected_recipe_collection_qs)
    
    def test_filter_recipe_collection_by_member_with_member_no_friends(self):
        params = {"member": self.logged_user, "logged_user": None}
        expected_recipe_collection_qs = self.initial_recipe_collection_qs.filter(member=self.logged_user)
        
        self._test_filter_recipe_collection_by_member(params, expected_recipe_collection_qs)

class GetFilteredRecipeCollectionQsTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        ingredient = Ingredient.objects.create(name="carotte")
        recipe_ingredient = RecipeIngredient.objects.create(ingredient=ingredient, quantity=1, unit="u")
        self.recipe1 = Recipe.objects.create(title="Recette 1", category="plat")
        self.recipe2 = Recipe.objects.create(title="Recette 2", category="dessert")
        self.recipe3 = Recipe.objects.create(title="Recette 3", category="dessert")
        self.recipe2.recipe_ingredient.add(recipe_ingredient)
        self.recipe3.recipe_ingredient.add(recipe_ingredient)

        for collection_name, _ in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES:
            RecipeCollectionEntry.objects.create(
                collection_name=collection_name,
                member=self.member,
                recipe=self.recipe2,
                saving_date="2025-02-01"
            )
            RecipeCollectionEntry.objects.create(
                collection_name=collection_name,
                member=self.member,
                recipe=self.recipe3,
                saving_date="2025-02-02"
            )
    
    def _test_get_filtered_recipe_collection_qs(self, partial_form_data, collection_name, form_class):
        with patch.object(utils, path.GET_INGREDIENT_INPUTS) as mock_get_ingredient_inputs, \
        patch.object(utils, path.GET_RECIPE_COLLECTION_BY_SORT_ORDER) as mock_get_recipe_collection_by_sort_order,\
        patch.object(utils, path.FILTER_RECIPE_COLLECTION_BY_MEMBER) as mock_filter_recipe_collection_by_member:
            mock_get_ingredient_inputs.return_value = {"ingredient_1": "carotte"}
            mock_get_recipe_collection_by_sort_order.return_value = "mock_get_recipe_collection_by_sort_order"
            mock_filter_recipe_collection_by_member.return_value = RecipeCollectionEntry.objects\
                .filter(collection_name=collection_name)\
                .order_by("recipe__title")

            form_data = partial_form_data.copy()
            form_data["member"] = self.member
            form_data["collection_name"] = collection_name
            form = form_class(form_data)
            form.is_valid()
            recipe_collection_qs = get_filtered_recipe_collection_qs(form)

            filter_data = {
                f"recipe__{key}" if "ingredient" not in key else "recipe__recipe_ingredient__ingredient__name": value
                for key, value in partial_form_data.items()
            }
            
            expected_recipe_collection_entries = RecipeCollectionEntry.objects\
                .filter(collection_name=collection_name, **filter_data)\
                .order_by("recipe__title")
            
            if collection_name == "history":
                distinct_ids = expected_recipe_collection_entries.values("recipe", "saving_date").annotate(min_id=Min("id")).values_list("min_id", flat=True)
            else:
                distinct_ids = expected_recipe_collection_entries.values("recipe").annotate(min_id=Min("id")).values_list("min_id", flat=True)
            expected_recipe_collection_entries = expected_recipe_collection_entries.filter(id__in=distinct_ids)
        
            self.assertEqual(list(recipe_collection_qs), list(expected_recipe_collection_entries))
    
    def test_get_filtered_recipe_collection_qs_cases(self):
        for partial_form_data in [
            {
                "category": "dessert"
            },
            {
                "category": "dessert",
                "title": "Recette 2"
            },
            {
                "category": "dessert",
                "title": "Recette 2",
                "ingredient_1": "carotte"
            },
            {
                "category": "plat",
                "ingredient_1": "carotte"
            }
            ]:
                for form_class, collection_choices in [
                     (SearchRecipeForm, SearchRecipeForm.FORM_COLLECTION_CHOICES),
                     (ShowRecipeCollectionForm, RecipeCollectionEntry.MODEL_COLLECTION_CHOICES)
                ]:
                    for collection_name, _ in collection_choices:
                        with self.subTest(f"case: {partial_form_data}, {form_class}, {collection_name}"):
                            self._test_get_filtered_recipe_collection_qs(partial_form_data, collection_name, form_class)

class GetFilteredRecipeQsTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        ingredient = Ingredient.objects.create(name="carotte")
        recipe_ingredient = RecipeIngredient.objects.create(ingredient=ingredient, quantity=1, unit="u")
        self.recipe1 = Recipe.objects.create(title="Recette 1", category="plat")
        self.recipe2 = Recipe.objects.create(title="Recette 2", category="dessert")
        self.recipe3 = Recipe.objects.create(title="Recette 3", category="dessert")
        self.recipe2.recipe_ingredient.add(recipe_ingredient)
        self.recipe3.recipe_ingredient.add(recipe_ingredient)
        RecipeCollectionEntry.objects.create(
            member=self.member,
            recipe=self.recipe2,
            saving_date="2025-02-01"
        )
        RecipeCollectionEntry.objects.create(
            member=self.member,
            recipe=self.recipe3,
            saving_date="2025-02-02"
        )

    def _test_get_filtered_recipe_qs(self, partial_form_data, member):
        with patch.object(utils, path.GET_INGREDIENT_INPUTS) as mock_get_ingredient_inputs, \
        patch.object(utils, path.FILTER_RECIPE_COLLECTION_BY_MEMBER) as mock_filter_recipe_collection_by_member:
            mock_get_ingredient_inputs.return_value = {"ingredient_1": "carotte"}
            mock_filter_recipe_collection_by_member.return_value = RecipeCollectionEntry.objects\
                .filter(member=member)

            form_data = partial_form_data.copy()
            form_data["member"] = member
            form = SearchRecipeForm(form_data)
            form.is_valid()
            recipe_qs = get_filtered_recipe_qs(form, "mock_logged_user")

            filter_data = {
                f"{key}" if "ingredient" not in key else "recipe_ingredient__ingredient__name": value
                for key, value in partial_form_data.items()
            }
            
            if member:
                expected_recipe_collection_entries = mock_filter_recipe_collection_by_member.return_value
                expected_recipe_ids = expected_recipe_collection_entries.values_list("recipe", flat=True)
                expected_recipe_qs = Recipe.objects.filter(id__in=expected_recipe_ids)
            else:
                expected_recipe_qs = Recipe.objects.all()
            
            expected_recipe_qs = expected_recipe_qs.filter(**filter_data).order_by("title")
        
            self.assertEqual(list(recipe_qs), list(expected_recipe_qs))
        
    def test_get_filtered_recipe_qs_cases(self):
        for partial_form_data in [
            {"category": "dessert"},
            {
                "category": "dessert",
                "title": "Recette 2"
            },
            {
                "category": "dessert",
                "title": "Recette 2",
                "ingredient_1": "carotte"
            },
            {
                "category": "plat",
                "ingredient_1": "carotte"
            },
        ]:
            with self.subTest(msg=f"{partial_form_data}, {self.member}"):
                self._test_get_filtered_recipe_qs(partial_form_data, member=self.member)
            with self.subTest(msg=f"{partial_form_data}, member: 'None'"):
                self._test_get_filtered_recipe_qs(partial_form_data, member=None)

class HandleSearchRecipeRequestTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        for ind in range(1, 3):
            Recipe.objects.create(title=f"recette plat_{ind}", category="plat")
        self.factory = RequestFactory()

    def test_handle_search_recipe_request_form_invalid(self):        
        request = self.factory.get("/", {"category": "unvalid_category"})
        form, recipe_collection_qs, recipe_qs = handle_search_recipe_request(request, self.member)
        
        self.assertIsInstance(form, SearchRecipeForm)
        self.assertIsNotNone(form.errors)
        self.assertEqual(recipe_collection_qs.count(), 0)
        self.assertEqual(recipe_qs.count(), 2)
        self.assertEqual(list(recipe_qs), list(Recipe.objects.all().order_by("title")))     
 
    @patch.object(utils, path.GET_FILTERED_RECIPE_COLLECTION_QS)
    @patch.object(utils, path.GET_FILTERED_RECIPE_QS)
    def test_handle_search_recipe_request_no_collection_name(
        self,
        mock_get_filtered_recipe_qs,
        mock_get_filtered_recipe_collection_qs
        ):
        mock_get_filtered_recipe_qs.return_value = "mock_get_filtered_recipe_qs"
        mock_get_filtered_recipe_collection_qs.return_value = "mock_get_filtered_recipe_collection_qs"
    
        request = self.factory.get("/")
        form, recipe_collection_qs, recipe_qs = handle_search_recipe_request(request, self.member)
        
        self.assertIsInstance(form, SearchRecipeForm)
        self.assertTrue(form.is_valid())
        self.assertEqual(recipe_collection_qs.count(), 0)
        self.assertEqual(recipe_qs, "mock_get_filtered_recipe_qs")

    @patch.object(utils, path.GET_FILTERED_RECIPE_COLLECTION_QS)
    @patch.object(utils, path.GET_FILTERED_RECIPE_QS)
    def test_handle_search_recipe_request_with_collection_name(
        self,
        mock_get_filtered_recipe_qs,
        mock_get_filtered_recipe_collection_qs
        ):
        mock_get_filtered_recipe_qs.return_value = "mock_get_filtered_recipe_qs"
        mock_get_filtered_recipe_collection_qs.return_value = "mock_get_filtered_recipe_collection_qs"
    
        request = self.factory.get("/", {"collection_name": "album"})
        form, recipe_collection_qs, recipe_qs = handle_search_recipe_request(request, self.member)
        
        self.assertIsInstance(form, SearchRecipeForm)
        self.assertTrue(len(form.errors)==0)
        self.assertEqual(recipe_collection_qs, "mock_get_filtered_recipe_collection_qs")
        self.assertEqual(recipe_qs.count(), 0)

class HandleShowRecipeCollectionRequestTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        for ind in range(1, 3):
            Recipe.objects.create(title=f"recette plat_{ind}", category="plat")
        self.factory = RequestFactory()

    def test_handle_show_recipe_collection_request_form_invalid(self):        
        request = self.factory.post("/", {"collection_name": "unvalid_collection_name"})
        form, recipe_collection_qs = handle_show_recipe_collection_request(request)
        
        self.assertIsInstance(form, ShowRecipeCollectionForm)
        self.assertFalse(len(form.errors)==0)
        self.assertEqual(recipe_collection_qs.count(), 0)
    
    @patch.object(utils, path.GET_FILTERED_RECIPE_COLLECTION_QS)
    def test_handle_show_recipe_collection_request_form_valid(self, mock_get_filtered_recipe_collection_qs):
        mock_get_filtered_recipe_collection_qs.return_value = "mock_get_filtered_recipe_collection_qs"

        request = self.factory.post("/", {"member": self.member.id, "collection_name":"album"})
        form, recipe_collection_qs = handle_show_recipe_collection_request(request)
        
        self.assertIsInstance(form, ShowRecipeCollectionForm)
        self.assertTrue(len(form.errors)==0)
        self.assertEqual(recipe_collection_qs, "mock_get_filtered_recipe_collection_qs")

class CheckRequestValidityTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _test_check_request_validity_status_code_400_expected(self, params, expected_message):
        request = self.factory.post("/", params)
        logged_user, recipe_id, collection_name, json_response = check_request_validity(request)
        self.assertIsNotNone(json_response)
        self.assertIsInstance(json_response, JsonResponse)

        response_data = json.loads(json_response.content)
        self.assertEqual(json_response.status_code, 400)
        self.assertIn("message", response_data)
        self.assertEqual(response_data["message"], expected_message)

    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_without_logged_user(self, mock_get_logged_user):
        mock_get_logged_user.return_value = None

        self._test_check_request_validity_status_code_400_expected(
            params=None,
            expected_message="Aucun utilisateur connecté."
            )
    
    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_without_recipe_id(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"

        self._test_check_request_validity_status_code_400_expected(
            params={"collection_name": "mocked_collection_name"},
            expected_message="ID de recette manquant."
            )

    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_without_collection_name(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"

        self._test_check_request_validity_status_code_400_expected(
            params={"recipe_id": "mocked_recipe_id"},
            expected_message= "Nom de la collection manquant."
            )
    
    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_invalid_collection_name(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"
        params = {
            "recipe_id": "mocked_recipe_id",
            "collection_name": "unvalid_collection_name"
        }

        self._test_check_request_validity_status_code_400_expected(
            params=params,
            expected_message= f"Le modèle 'unvalid_collection_name' est inconnu."
            )
    
    @patch.object(utils, path.GET_LOGGED_USER)
    def test_check_request_validity_valid_data(self, mock_get_logged_user):
        mock_get_logged_user.return_value =  "mocked_user"
        params = {
            "recipe_id": "mocked_repipe_id",
        }

        for collection_name, _ in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES:
            params["collection_name"] = collection_name
            request = self.factory.post("/", params)
            logged_user, recipe_id, collection_name, json_response = check_request_validity(request)
            
            self.assertIsNone(json_response)
            self.assertEqual(logged_user, "mocked_user")
            self.assertEqual(recipe_id, "mocked_repipe_id")
            self.assertIn(collection_name, dict(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES).keys())

class UpdateCollectionTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="test_user", password="password")
        self.recipe = Recipe.objects.create(title="recette test", category="plat")
        self.factory = RequestFactory()
    
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

    def test_update_collection_without_collection_name(self):
        mocked_request_validity_json = JsonResponse({"message": "Nom de la collection manquant."}, status=400)
        for action in ["add", "remove"]:
             for collection_name, _ in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES:
                
                self._test_update_collection(
                    action=action,
                    collection_name=collection_name,
                    mocked_request_validity_json=mocked_request_validity_json,
                    expected_message="Nom de la collection manquant.",
                    expected_status=400
                )
            
    def test_update_collection_cases_1(self):
        for collection_name, collection_title in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES:
            test_cases = [
                {
                    "desc": f"invalid_action, {collection_name}",
                    "params": {
                        "action": "invalid_action",
                        "collection_name": collection_name,
                        "mocked_request_validity_json": None,
                        "expected_message": "Une erreur est survenue: 'Action non valide'.",
                        "expected_status": 400
                    }
                },
                {
                    "desc": f"add, {collection_name}",
                    "params": {
                        "action": "add",
                        "collection_name": collection_name,
                        "mocked_request_validity_json": None,
                        "expected_message": f"La recette a été ajoutée à votre {collection_title}.",
                        "expected_status": 200
                    }
                },
                {
                    "desc": f"remove, {collection_name}",
                    "params": {
                        "action": "remove",
                        "collection_name": collection_name,
                        "mocked_request_validity_json": None,
                        "expected_message": f"La recette ne fait pas partie de votre {collection_title}.",
                        "expected_status": 200
                    }
                }
            ]
            for case in test_cases:
                with self.subTest(msg=case["desc"]):
                    with transaction.atomic():
                        self._test_update_collection(**case["params"])
                        transaction.set_rollback(True)

    def test_update_collection_cases_2(self):
        for collection_name, collection_title in RecipeCollectionEntry.MODEL_COLLECTION_CHOICES:
            RecipeCollectionEntry.objects.create(collection_name=collection_name, member=self.member, recipe=self.recipe)
            test_cases = [
                {
                    "desc": f"add, {collection_name}",
                    "params": {
                        "action": "add",
                        "collection_name": collection_name,
                        "mocked_request_validity_json": None,
                        "expected_message": f"La recette fait déjà partie de votre {collection_title}.",
                        "expected_status": 200
                    }
                },
                {
                    "desc": f"remove, {collection_name}",
                    "params": {
                        "action": "remove",
                        "collection_name": collection_name,
                        "mocked_request_validity_json": None,
                        "expected_message": f"La recette a été supprimée de votre {collection_title}.",
                        "expected_status": 200
                        }
                }
            ]
            for case in test_cases:
                with self.subTest(msg=case["desc"]):
                    with transaction.atomic():
                        self._test_update_collection(**case["params"])
                        transaction.set_rollback(True)

       


