"""
Unit tests for the views Django contained in the module web.py..
"""
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase
from django.urls import reverse
from recipe_journal.models import Member, Recipe
from unittest.mock import patch
from recipe_journal.forms import AddFriendForm, FilterRecipeCollectionForm, RegistrationForm, SearchRecipeForm
import recipe_journal.utils.utils as ut
from recipe_journal.tests.test_config.mock_function_paths import MockFunctionPathManager

path = MockFunctionPathManager()

class LoginViewTest(TestCase):
    def setUp(self):
        Member.objects.create(username="testuser", password=make_password("password"))

    def test_login_valid_user(self):
        response = self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/welcome")

    def test_login_invalid_user(self):
        response = self.client.post(reverse("login"), {"username": "wronguser", "password": "wrongpass"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="login-page"')
        self.assertContains(response, "Identifiant ou mot de passe erroné.")

    def test_login_empty_form(self):
        response = self.client.post(reverse("login"))
        self.assertEqual(response.status_code, 200) 
        self.assertContains(response, 'id="login-page"')
    
    def test_login_method_get(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200) 
        self.assertContains(response, 'id="login-page"')

class LogoutViewTest(TestCase):
    def setUp(self):
        Member.objects.create(username="testuser", password=make_password("password"))

    def test_logout_user_not_logged(self):
        response = self.client.get(reverse("logout"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/welcome")

    def test_logout_user_logged(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        
        self.assertIn("logged_user_id", self.client.session)

        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/welcome")
        self.assertNotIn("logged_user_id", self.client.session)

class RegisterViewTest(TestCase):
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

class ModifyProfileViewTest(TestCase):
    def setUp(self):
        Member.objects.create(username="testuser", password=make_password("password"))
        Member.objects.create(username="existing_user", password=make_password("password"))
    
    def test_modify_profile_user_not_logged(self):
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
    
    def test_modify_profile_same_username_same_password(self, ):
        form_data = {
            "username": "testuser",
            "former_password": "password",
            "new_password": "password",
            "confirm_new_password": "password"
            }
        self._test_modify_profile_success(form_data)
    
    def test_modify_profile_new_username_same_password(self, ):
        form_data = {
            "username": "new_username",
            "former_password": "password",
            "new_password": "password",
            "confirm_new_password": "password"
            }
        self._test_modify_profile_success(form_data)
    
    def test_modify_profile_same_username_new_password(self, ):
        form_data = {
            "username": "testuser",
            "former_password": "password",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        self._test_modify_profile_success(form_data)
    
    def test_modify_profile_new_username_new_password(self, ):
        form_data = {
            "username": "new_username",
            "former_password":  "password",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        self._test_modify_profile_success(form_data)

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

    def test_modify_profile_password_unvalid(self):
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

    def test_modify_profile_new_password_unvalid(self):
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

class WelcomeViewTest(TestCase):
    @patch.object(ut, path.GET_LOGGED_USER)
    @patch.object(ut, path.GET_DAILY_RANDOM_SAMPLE)
    def test_welcome_view(self, mock_get_daily_random_sample, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"
        mock_get_daily_random_sample.side_effect = [
            [1, 2],
            [3, 4]
        ]

        for i in range(1, 5):
            Recipe.objects.create(id= i, title=f"Recipe {i}", category="dessert")

        response = self.client.get(reverse("welcome"))

        self.assertEqual(response.status_code, 200)
        mock_get_daily_random_sample.assert_any_call(2)
        self.assertEqual(mock_get_daily_random_sample.call_count, 2)

        context = response.context
        self.assertEqual(len(context['top_recipe_list']), 2)
        self.assertEqual(len(context['thumbnail_recipes']), 2)
        self.assertEqual(context['MEDIA_URL'], settings.MEDIA_URL)

        self.assertEqual(context['top_recipe_list'][0].title, "Recipe 1")
        self.assertEqual(context['top_recipe_list'][1].title, "Recipe 2")
        self.assertEqual(context['thumbnail_recipes'][0].title, "Recipe 3")
        self.assertEqual(context['thumbnail_recipes'][1].title, "Recipe 4")

class AddRecipeViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password"))
    
    def test_add_recipe_method_get(self):
        response = self.client.get(reverse("add_recipe"))

        self.assertEqual(response.status_code, 405)

    @patch.object(ut, path.GET_LOGGED_USER)
    def test_add_recipe_user_not_logged(self, mock_get_logged_user):
        mock_get_logged_user.return_value = None
        response = self.client.post(reverse("add_recipe"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")
    
    @patch.object(ut, path.GET_LOGGED_USER)
    @patch.object(ut, path.PREPARE_RECIPE_FORMS)
    @patch.object(ut, path.ARE_FORMS_VALID)
    def test_add_recipe_form_unvalid(self, mock_are_forms_valid, mock_prepare_recipe_forms, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"
        mock_prepare_recipe_forms.return_value = ("mocked_recipe_form", "mocked_ingredient_forms", "mocked_manage_recipe_collection_form")
        mock_are_forms_valid.return_value = False
        response = self.client.post(reverse("add_recipe"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="add-recipe-page"')

        context = response.context
        self.assertEqual(context["logged_user"], "mocked_user")
        self.assertEqual(context["recipe_form"], "mocked_recipe_form")
        self.assertEqual(context["recipe_ingredient_form_list"], "mocked_ingredient_forms")
        self.assertEqual(context[ "manage_recipe_collection_form"], "mocked_manage_recipe_collection_form")
                         

    def test_add_recipe_form_valid(self):
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

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/show-confirmation-page")

class ShowConfirmationPageTest(TestCase):
    def test_show_confirmation_page_user_not_logged(self):
        response = self.client.post(reverse("show_confirmation_page"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")
    
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_show_confirmation_page_user_logged(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mock_user"

        response = self.client.post(reverse("show_confirmation_page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="confirmation-page"')

class ShowRecipeTest(TestCase):
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_show_recipe_valid_id(self,  mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"
        recipe = Recipe.objects.create(title="recette test", category="dessert")
        recipe_id = recipe.id

        self.assertEqual(len(Recipe.objects.filter(id=recipe_id)), 1)
        response = self.client.get(reverse("show_recipe"), {"recipe-id": recipe_id})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="recipe-page"')

        context = response.context
        self.assertEqual(context["logged_user"], "mocked_user")
        self.assertEqual(context["recipe"], recipe)
        self.assertEqual(context["MEDIA_URL"], settings.MEDIA_URL)

    
    def test_show_recipe_id_unvalid(self):
        recipe_id = 4

        response = self.client.get(reverse("show_recipe"), {"recipe-id": recipe_id})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/welcome")
        
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
    def test_show_friends_user_not_logged(self, mock_get_logged_user):
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
        self.assertIn("form", context)
        self.assertIsInstance(context["form"], AddFriendForm)
    
    @patch.object(ut, path.HANDLE_ADD_FRIEND_REQUEST)
    def test_show_friends_add_friend(self, mock_handle_add_friend_request):        
        mock_handle_add_friend_request.side_effect = self.side_effect_add_friend
        response = self.client.post(reverse("show_friends"), {"username_to_add":"friend"})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="show-friends-page"')
        self.assertIn(self.friend, self.member.friends.all())

        context = response.context
        self.assertEqual(self.member, context["logged_user"])
        self.assertIn(self.friend, context["friends"])
        self.assertEqual(context["form"], "mock_form")
    

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
        self.assertNotIn(self.friend, context["friends"])

class ShowMemberRecipeCollectionTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password"))
        self.client.post(reverse("login"), {"username":"testuser", "password":"password"})

    @patch.object(ut, path.GET_LOGGED_USER)
    def test_show_member_recipe_collection_user_not_logged(self, mock_get_logged_user):
        mock_get_logged_user.return_value = None
        response = self.client.post(reverse("show_recipe_collection"))
        
        mock_get_logged_user.assert_called_once()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")
    
    
    @patch.object(ut, path.FILTER_MEMBER_RECIPE_COLLECTION)
    def test_show_member_recipe_collection_form_empty(self, mock_filter_member_recipe_collection):
        mock_empty_form = FilterRecipeCollectionForm()
        mock_empty_form.is_valid()
        mock_filter_member_recipe_collection.return_value = mock_empty_form, "mock_recipe_collection_entries"
        response = self.client.post(reverse("show_recipe_collection"))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="show-recipe-collection-page"')

        context = response.context
        self.assertEqual(context["logged_user"], self.member)
        self.assertIn("member", context)
        self.assertEqual(context["form"], mock_empty_form)
        self.assertEqual(context["recipe_entries"], "mock_recipe_collection_entries")
        self.assertIn('id="form-filter-recipe-collection"', response.content.decode())
    
    @patch.object(ut, path.FILTER_MEMBER_RECIPE_COLLECTION)
    def test_show_member_recipe_collection_form_with_data(self, mock_filter_recipe_collection):
        fom_data = {
            "title": "mock recette",
            "category": "dessert",
            "collection_name": "album",
            "member": self.member,
            "ingredient_1": "mock ingredient"
            }
        mock_form = FilterRecipeCollectionForm(fom_data)
        mock_form.is_valid()
        mock_filter_recipe_collection.return_value = mock_form, "mock_recipe_collection_entries"
        response = self.client.post(reverse("show_recipe_collection"))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="show-recipe-collection-page"')

        context = response.context
        self.assertEqual(context["member"], self.member)
        self.assertEqual(context["collection_name"], "album")
        self.assertEqual(context["form"], mock_form)
        self.assertIn("mock recette", str(context["form"]))
        self.assertIn('id="form-filter-recipe-collection"', response.content.decode())

class SearchRecipeTest(TestCase):
    def setUp(self):
        for i in range(1, 5):
            Recipe.objects.create(id= i, title=f"Recipe {i}", category="dessert")
    
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_search_recipe_user_not_logged(self, mock_get_logged_user):
        mock_get_logged_user.return_value = None
        response = self.client.get(reverse("search_recipe"))
        
        mock_get_logged_user.assert_called_once()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login")
    
    @patch.object(ut, path.GET_LOGGED_USER)
    def test_search_recipe_method_post(self, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"
        response = self.client.post(reverse("search_recipe"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="search-recipe-page"')

        context = response.context
        self.assertIn("logged_user", context)
        self.assertEqual(context["logged_user"], "mocked_user")

        context_recipe_ids = [recipe.id for recipe in response.context["thumbnail_recipes"]]

        self.assertEqual(list(range(1, 5)), sorted(context_recipe_ids))
        self.assertIn("thumbnail_recipes", response.context)
        
        self.assertIn("form", context)
        self.assertIsInstance(context["form"], SearchRecipeForm)

    @patch.object(ut, path.GET_LOGGED_USER)
    @patch.object(ut, path.HANDLE_SEARCH_RECIPE_REQUEST)
    def test_search_recipe_method_get(self, mock_handle_search_recipe_request, mock_get_logged_user):
        mock_get_logged_user.return_value = "mocked_user"
        mock_handle_search_recipe_request.return_value = SearchRecipeForm({"title":"recette test"}), Recipe.objects.filter(id__in=[1, 2])

        response = self.client.get(reverse("search_recipe"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="search-recipe-page"')
        mock_handle_search_recipe_request.assert_called_once()

        context = response.context
        self.assertIn("logged_user", context)
        self.assertEqual(context["logged_user"], "mocked_user")

        context_recipe_ids = [recipe.id for recipe in response.context["thumbnail_recipes"]]

        self.assertEqual([1, 2], sorted(context_recipe_ids))
        self.assertIn("thumbnail_recipes", response.context)
        
        self.assertIn("form", context)
        self.assertIsInstance(context["form"], SearchRecipeForm)
        self.assertIn("recette test", str(context["form"]))
        self.assertIn('id="form-search-recipe"', response.content.decode())



  

