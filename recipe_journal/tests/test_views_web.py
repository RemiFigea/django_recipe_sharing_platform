"""
Unit tests for the web.py module.
"""
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from recipe_journal.forms import AddFriendForm, AddRecipeToCollectionForm, RecipeCombinedForm, RecipeIngredientForm
from recipe_journal.forms import RegistrationForm, ShowRecipeCollectionForm, SearchRecipeForm
from recipe_journal.models import Member, Recipe, RecipeCollectionEntry
from recipe_journal.tests.test_config.mock_function_paths import MockFunctionPathManager
import recipe_journal.utils.utils as ut
from unittest.mock import patch

path = MockFunctionPathManager()

class LoginTest(TestCase):
    def setUp(self):
        Member.objects.create(username="testuser", password=make_password("password"))

    def test_login_form_valid(self):
        response = self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/welcome")

    def test_login_form_invalid(self):
        response = self.client.post(reverse("login"), {"username": "wronguser", "password": "wrongpass"})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="login-page"')
        self.assertContains(response, "Identifiant ou mot de passe erroné.")

    def test_login_form_empty(self):
        response = self.client.post(reverse("login"))
        
        self.assertEqual(response.status_code, 200) 
        self.assertContains(response, 'id="login-page"')
    
    def test_login_method_get(self):
        response = self.client.get(reverse("login"))
        
        self.assertEqual(response.status_code, 200) 
        self.assertContains(response, 'id="login-page"')

class LogoutTest(TestCase):
    def setUp(self):
        Member.objects.create(username="testuser", password=make_password("password"))

    def test_logout_without_logged_user(self):
        response = self.client.get(reverse("logout"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/welcome")

    def test_logout_with_logged_user(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        
        self.assertIn("logged_user_id", self.client.session)

        response = self.client.get(reverse("logout"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/welcome")
        self.assertNotIn("logged_user_id", self.client.session)

class RegisterTest(TestCase):
    def setUp(self):
        Member.objects.create(username="testuser", password=make_password("password"))

    def test_register_method_get(self):
        response = self.client.get(reverse("register"), {"username": "new_username", "password": "password"})
    
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="registration-page"')

        context = response.context
        
        self.assertIn("form", context)
        self.assertIsInstance(context["form"], RegistrationForm)

    def test_register_username_available(self):
        response = self.client.post(reverse("register"), {"username": "new_username", "password": "password"})
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")
        self.assertTrue(Member.objects.filter(username="new_username").exists())
   
    def test_register_username_unavailable(self):
        response = self.client.post(reverse("register"), {"username": "testuser", "password": "password"})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="registration-page"')
        self.assertContains(response, "Identifiant non disponible.")

        context = response.context
        
        self.assertIn("form", context)
        self.assertIsInstance(context["form"], RegistrationForm)

class ModifyProfileTest(TestCase):
    def setUp(self):
        Member.objects.create(username="testuser", password=make_password("password"))
        Member.objects.create(username="existing_user", password=make_password("password"))
    
    def test_modify_profile_without_logged_user(self):
        response = self.client.post(reverse("modify_profile"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")

    def _test_modify_profile_success(self, form_data):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        username = form_data["username"]
        new_password = form_data["new_password"]
        response = self.client.post(reverse("modify_profile"), form_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")
        self.assertTrue(Member.objects.filter(username=username).exists())

        updated_member = Member.objects.get(username=username)

        self.assertTrue(check_password(new_password, updated_member.password))

        if username != "testuser":
            self.assertFalse(Member.objects.filter(username="testuser").exists())
    
    def test_modify_profile_success_cases(self):
        test_cases = [
            {
                "desc": "same username, same password",
                "form_data": {
                    "username": "testuser",
                    "former_password": "password",
                    "new_password": "password",
                    "confirm_new_password": "password"
                }
            },
            {
                "desc": "new username, same password",
                "form_data": {
                    "username": "new_username",
                    "former_password": "password",
                    "new_password": "password",
                    "confirm_new_password": "password"
                }
            },
            {
                "desc": "same username, new password",
                "form_data": {
                    "username": "testuser",
                    "former_password": "password",
                    "new_password": "new_password",
                    "confirm_new_password": "new_password"
                }
            },
            {
                "desc": "new username, new password",
                "form_data": {
                    "username": "new_username",
                    "former_password": "password",
                    "new_password": "new_password",
                    "confirm_new_password": "new_password"
                }
            }
        ]
        for case in test_cases:
            with self.subTest(msg=case["desc"]):
                with transaction.atomic():
                    self._test_modify_profile_success(case["form_data"])
                    transaction.set_rollback(True)

    def test_modify_profile_username_unavailable(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        form = {
            "username": "existing_user",
            "former_password": "password",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        response = self.client.post(reverse("modify_profile"), form)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="modify-profile-page"')
        self.assertContains(response, "Identifiant non disponible.")
        self.assertTrue(Member.objects.filter(username="testuser").exists())

    def test_modify_profile_password_invalid(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        form = {
            "username": "testuser",
            "former_password": "wrong_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        response = self.client.post(reverse("modify_profile"), form)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="modify-profile-page"')
        self.assertContains(response, "Ancien mot de passe erroné.")
        self.assertTrue(Member.objects.filter(username="testuser").exists())

    def test_modify_profile_new_password_invalid(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        form = {
            "username": "testuser",
            "former_password": "password",
            "new_password": "new_password",
            "confirm_new_password": "unconsistent_new_password"
            }
        response = self.client.post(reverse("modify_profile"), form)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="modify-profile-page"')
        self.assertContains(response, "Les nouveaux mots de passe ne correspondent pas.")
        self.assertTrue(Member.objects.filter(username="testuser").exists())

class WelcomeTest(TestCase):
    @patch.object(ut, path.GET_LOGGED_USER)
    @patch.object(ut, path.GET_DAILY_RANDOM_SAMPLE)
    def test_welcome(self, mock_get_daily_random_sample, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"
        mock_get_daily_random_sample.return_value = list(range(1, 5))

        for i in range(1, 5):
            Recipe.objects.create(id= i, title=f"Recipe {i}", category="dessert")

        response = self.client.get(reverse("welcome"))

        self.assertEqual(response.status_code, 200)
        mock_get_daily_random_sample.assert_called()

        context = response.context
        
        self.assertIn("logged_user", context)
        self.assertEqual(context["logged_user"], "mocked_user")
        self.assertIn("top_recipe_qs", context)
        self.assertEqual(context["top_recipe_qs"].count(), 2)
        self.assertEqual(set(context["top_recipe_qs"].values_list("title", flat=True)), {"Recipe 1", "Recipe 2"})
        self.assertIn("thumbnail_recipe_qs", context)
        self.assertEqual(context["thumbnail_recipe_qs"].count(), 2)
        self.assertEqual(set(context["thumbnail_recipe_qs"].values_list("title", flat=True)), {"Recipe 3", "Recipe 4"})
        self.assertEqual(context["MEDIA_URL"], settings.MEDIA_URL)

class AddRecipeTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password"))
    
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_add_recipe_user_without_logged_user(self, mock_get_logged_user):
        mock_get_logged_user.return_value = None
        response = self.client.post(reverse("add_recipe"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")
    
    @patch.object(ut, path.ARE_FORMS_VALID)
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_add_recipe_method_get(self, mock_get_logged_user, mock_are_forms_valid):
        mock_get_logged_user.return_value = "mocked_user"
        mock_are_forms_valid.return_value = "mock_are_forms_valid"

        response = self.client.get(reverse("add_recipe"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="add-recipe-page"')

        context = response.context

        self.assertIsInstance(context["recipe_form"], RecipeCombinedForm)
        self.assertIsInstance(context["recipe_ingredient_form_list"][0], RecipeIngredientForm)
        self.assertIsInstance(context[ "manage_recipe_collection_form"], AddRecipeToCollectionForm)
        mock_are_forms_valid.assert_not_called()
    
    
    @patch.object(ut, path.ARE_FORMS_VALID)
    @patch.object(ut, path.PREPARE_RECIPE_FORMS)
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_add_recipe_with_form_invalid(self, mock_get_logged_user, mock_prepare_recipe_forms, mock_are_forms_valid):
        mock_get_logged_user.return_value = "mocked_user"
        mock_prepare_recipe_forms.return_value = ("mocked_recipe_form", "mocked_ingredient_forms", "mocked_manage_recipe_collection_form")
        mock_are_forms_valid.return_value = False
        
        response = self.client.post(reverse("add_recipe"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="add-recipe-page"')

        context = response.context

        mock_are_forms_valid.assert_called()
        self.assertEqual(context["logged_user"], "mocked_user")
        self.assertEqual(context["recipe_form"], "mocked_recipe_form")
        self.assertEqual(context["recipe_ingredient_form_list"], "mocked_ingredient_forms")
        self.assertEqual(context[ "manage_recipe_collection_form"], "mocked_manage_recipe_collection_form")

    @patch.object(ut, path.ADD_RECIPE_TO_COLLECTIONS)
    @patch.object(ut, path.SAVE_RECIPE_AND_INGREDIENTS)
    @patch.object(ut, path.ARE_FORMS_VALID)
    @patch.object(ut, path.PREPARE_RECIPE_FORMS)
    @patch.object(ut, path.GET_LOGGED_USER)                    
    def test_add_recipe_with_form_valid(
        self,
        mock_get_logged_user,
        mock_prepare_recipe_forms,
        mock_are_forms_valid,
        mock_save_recipe_and_ingredients,
        mock_add_recipe_to_collections
        ):
        mock_get_logged_user.return_value = "mocked_user"
        mock_prepare_recipe_forms.return_value = ("mocked_recipe_form", "mocked_ingredient_forms", "mocked_manage_recipe_collection_form")
        mock_are_forms_valid.return_value = True
        mock_save_recipe_and_ingredients.return_value = "mock_save_recipe_and_ingredients",
        mock_add_recipe_to_collections.return_value = "mock_add_recipe_to_collections"

        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        form_data = {
            "title": "titre",
            "category": "dessert",
            "name": "ingredient",
            "quantity": 2,
            "unit": "kg",
            "add_to_album": True
            }

        response = self.client.post(reverse("add_recipe"), form_data)

        mock_save_recipe_and_ingredients.assert_called()
        mock_add_recipe_to_collections.assert_called()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/show-confirmation-page")

class ShowConfirmationPageTest(TestCase):
    def test_show_confirmation_page_without_logged_user(self):
        response = self.client.post(reverse("show_confirmation_page"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")
    
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_show_confirmation_page_with_logged_user(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mock_user"

        response = self.client.post(reverse("show_confirmation_page"))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="confirmation-page"')

class ShowRecipeTest(TestCase):
    def setUp(self):
        Recipe.objects.create(title="recette test", category="dessert")

    def test_show_recipe_method_post(self):
        response = self.client.post(reverse("show_recipe"))

        self.assertEqual(response.status_code, 405)
    
    def test_show_recipe_recipe_id_not_digit(self):
        response = self.client.get(reverse("show_recipe"), {"recipe-id": "unvalid type"})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/welcome")
    
    def test_show_recipe_recipe_id_inexisting(self):
        response = self.client.get(reverse("show_recipe"), {"recipe-id": 2})

        self.assertEqual(response.status_code, 404)
    
    def test_show_recipe_recipe_id_valid(self):
        response = self.client.get(reverse("show_recipe"), {"recipe-id": 1})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="show-recipe-page"')

        context = response.context

        self.assertIn("logged_user", context)
        self.assertIn("recipe", context)
        self.assertEqual(context["recipe"], Recipe.objects.get(id=1))
        self.assertEqual(context["MEDIA_URL"], settings.MEDIA_URL)
        
class ShowFriendsTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password"))
        self.friend = Member.objects.create(username="friend", password=make_password("password"))
        self.client.post(reverse("login"), {"username":"testuser", "password":"password"})

    def side_effect_add_friend(self, request, logged_user):
        self.member.friends.add(self.friend)      
        return "mock_form"

    def side_effect_remove_friend(self, request, logged_user):
        self.member.friends.remove(self.friend)
        return None

    @patch.object(ut, path.GET_LOGGED_USER)
    def test_show_friends_without_logged_user(self, mock_get_logged_user):
        mock_get_logged_user.return_value = None
        response = self.client.post(reverse("show_friends"), {"username_to_add":"friend"})

        mock_get_logged_user.assert_called_once()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")
    
    def test_show_friends_method_get(self):
        response = self.client.get(reverse("show_friends"), {"username_to_add":"friend"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="show-friends-page"')
        self.assertEqual(len(self.member.friends.all()), 0)

        context = response.context

        self.assertIn("logged_user", context)
        self.assertEqual(context["logged_user"], self.member)
        self.assertIn("friends", context)
        self.assertEqual(context["friends"].count(), 0)
        self.assertIn("form", context)
        self.assertIsInstance(context["form"], AddFriendForm)
        self.assertFalse(context["form"].is_valid())
    
    @patch.object(ut, path.HANDLE_ADD_FRIEND_REQUEST)
    def test_show_friends_add_friend(self, mock_handle_add_friend_request):        
        mock_handle_add_friend_request.side_effect = self.side_effect_add_friend
        response = self.client.post(reverse("show_friends"), {"username_to_add":"friend"})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="show-friends-page"')
        self.assertIn(self.friend, self.member.friends.all())

        context = response.context

        self.assertEqual(context["form"], "mock_form")
        self.assertEqual(context["friends"].count(), 1)
    
    @patch.object(ut, path.HANDLE_REMOVE_FRIEND_REQUEST)
    def test_show_friends_remove_friend(self, mock_handle_remove_friend_request):
        self.member.friends.add(self.friend)

        self.assertIn(self.friend, self.member.friends.all())

        mock_handle_remove_friend_request.side_effect = self.side_effect_remove_friend
        response = self.client.post(reverse("show_friends"), {"username_to_remove":"friend"})
        context = response.context

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="show-friends-page"')
        self.assertNotIn(self.friend, self.member.friends.all())

        context = response.context

        self.assertEqual(self.member, context["logged_user"])
        self.assertEqual(context["friends"].count(), 0)

class SearchRecipeTest(TestCase):
    def setUp(self):
        for i in range(1, 5):
            Recipe.objects.create(id= i, title=f"Recipe {i}", category="dessert")
        
    @patch.object(ut, path.HANDLE_SEARCH_RECIPE_REQUEST)
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_search_recipe_method_get(self, mock_get_logged_user, mock_handle_search_recipe_request):
        mock_get_logged_user.return_value = "mocked_user"
        mock_handle_search_recipe_request.return_value =\
            SearchRecipeForm({"title":"recette test"}), "mock_recipe_collection_qs", "mock_recipe_qs"

        response = self.client.get(reverse("search_recipe"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="search-recipe-page"')

        context = response.context

        self.assertIn("logged_user", context)
        self.assertEqual(context["logged_user"], "mocked_user")
        self.assertIn("collection_name", context)
        self.assertIn("thumbnail_recipe_qs", context)
        self.assertEqual(context["thumbnail_recipe_qs"], "mock_recipe_qs")
        self.assertIn("recipe_collection_qs", context)
        self.assertEqual(context["recipe_collection_qs"], "mock_recipe_collection_qs")
        self.assertIn("form", context)
        self.assertIsInstance(context["form"], SearchRecipeForm)
        self.assertIn("recette test", response.content.decode())
        self.assertEqual(context["MEDIA_URL"], settings.MEDIA_URL)
    
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_search_recipe_method_post(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"
        response = self.client.post(reverse("search_recipe"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="search-recipe-page"')

        context = response.context

        self.assertIn("thumbnail_recipe_qs", context)
        self.assertEqual(list(Recipe.objects.order_by("title")), list(context["thumbnail_recipe_qs"]))
        self.assertIn("recipe_collection_qs", context)
        self.assertEqual(context["recipe_collection_qs"].count(), 0)
        self.assertIn("form", context)
        self.assertIsInstance(context["form"], SearchRecipeForm)
        self.assertIn('id="form-search-recipe"', response.content.decode())
        self.assertEqual(context["MEDIA_URL"], settings.MEDIA_URL)

class ShowRecipeCollectionTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password"))
        self.client.post(reverse("login"), {"username":"testuser", "password":"password"})

    @patch.object(ut, path.GET_LOGGED_USER)
    def test_show_recipe_collection_without_logged_user(self, mock_get_logged_user):
        mock_get_logged_user.return_value = None
        response = self.client.post(reverse("show_recipe_collection"))
        
        mock_get_logged_user.assert_called_once()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")
    
    @patch.object(ut, path.HANDLE_SHOW_RECIPE_COLLECTION_REQUEST)
    def test_show_recipe_collection_method_post(self, mock_handle_show_recipe_collection_request):
        mock_form = ShowRecipeCollectionForm({"collection_name": "album", "member":self.member})
        mock_form.is_valid()
        mock_handle_show_recipe_collection_request.return_value = mock_form, "mock_recipe_collection_qs"
        
        response = self.client.post(reverse("show_recipe_collection"))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="show-recipe-collection-page"')

        context = response.context

        self.assertIn("logged_user", context)
        self.assertEqual(context["logged_user"], self.member)
        self.assertIn("member", context)
        self.assertEqual(context["member"], self.member)
        self.assertIn("collection_name", context)
        self.assertEqual(context["collection_name"], "album")
        self.assertIn("collection_title", context)
        self.assertEqual(context["collection_title"], dict(RecipeCollectionEntry.MODEL_COLLECTION_CHOICES).get("album"))
        self.assertIn("recipe_collection_qs", context)
        self.assertEqual(context["recipe_collection_qs"], "mock_recipe_collection_qs")
        self.assertIn("form", context)
        self.assertEqual(context["form"], mock_form)
        self.assertIn('id="form-show-recipe-collection"', response.content.decode())
        self.assertIn("album", response.content.decode())
        self.assertEqual(context["MEDIA_URL"], settings.MEDIA_URL)

    def test_show_recipe_collection_method_get(self):
        response = self.client.get(reverse("show_recipe_collection"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/welcome")





  

