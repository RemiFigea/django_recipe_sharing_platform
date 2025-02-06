"""
Unit tests for the views Django contained in the module web.py..
"""
from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase
from django.urls import reverse
from recipe_journal.forms import AddRecipeCombinedForm, AddRecipeIngredientForm, RecipeActionForm
from recipe_journal.models import Member
from unittest.mock import patch

class LoginViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser")
        self.member.password = make_password("password123")
        self.member.save()

    def test_login_valid_user(self):
        response = self.client.post(reverse("login"), {"username": "testuser", "password": "password123"})
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_user(self):
        response = self.client.post(reverse("login"), {"username": "wronguser", "password": "wrongpass"})
        self.assertEqual(response.status_code, 200) 
        self.assertContains(response, "Identifiant ou mot de passe erroné.")

class LogoutViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser")
        self.member.password = make_password("password123")
        self.member.save()

        self.client.post(reverse("login"), {"username": "testuser", "password": "password123"})
    
    def test_logout_success(self):
        self.assertIn("logged_user_id", self.client.session)

        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("logged_user_id", self.client.session)

class RegisterViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser")
        self.member.password = make_password("password123")
        self.member.save()

    def test_register_valid_username(self):
        response = self.client.post(reverse("register"), {"username": "newusername", "password": "password123"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Member.objects.filter(username="newusername").exists())
   
    def test_register_invalid_username(self):
        response = self.client.post(reverse("register"), {"username": "testuser", "password": "password123"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Identifiant non disponible.")

class ModifyProfileViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password123"))
        self.member.save()
        self.existing_member = Member.objects.create(username="existing_user", password=make_password("password123"))
        self.existing_member.save()
    
    def test_user_not_logged(self):
        response = self.client.post(reverse("modify_profile"))

        self.assertEqual(response.status_code, 302)

        redirect_url = response["Location"]
        self.assertEqual(redirect_url, "/login")
        
    def test_modify_profile_valid(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password123"})
        form_data = dict()
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
        form_data["same_username"] = {
            "username": "testuser",
            "former_password": "password123",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        form_data["new_username_and_password"] = {
            "username": "new_username",
            "former_password":  "new_password",
            "new_password": "new_password_again",
            "confirm_new_password": "new_password_again"
            }
        for form in form_data.values():
            self.member.refresh_from_db()
            username = form["username"]
            new_password = form["new_password"]
            response = self.client.post(reverse("modify_profile"), form)

            self.assertEqual(response.status_code, 302)
            self.assertTrue(Member.objects.filter(username=username).exists())

            updated_member = Member.objects.get(username=username)

            self.assertTrue(check_password(new_password, updated_member.password))

            if username != "testuser":
                self.assertFalse(Member.objects.filter(username="testuser").exists())

    def test_modify_profile_username_invalid(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password123"})
        form = {
            "username": "existing_user",
            "former_password": "password123",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        response = self.client.post(reverse("modify_profile"), form)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Identifiant non disponible.")
        self.assertTrue(Member.objects.filter(username="testuser").exists())

    def test_modify_profile_password_invalid(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password123"})
        form = {
            "username": "testuser",
            "former_password": "wrong_password",
            "new_password": "new_password",
            "confirm_new_password": "new_password"
            }
        response = self.client.post(reverse("modify_profile"), form)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ancien mot de passe erroné.")
        self.assertTrue(Member.objects.filter(username="testuser").exists())

    def test_modify_profile_new_password_invalid(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password123"})
        form = {
            "username": "testuser",
            "former_password": "password123",
            "new_password": "new_password",
            "confirm_new_password": "wrong_new_password"
            }
        response = self.client.post(reverse("modify_profile"), form)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Les nouveaux mots de passe ne correspondent pas.")
        self.assertTrue(Member.objects.filter(username="testuser").exists())

class WelcomeViewTest(TestCase):
    @patch("recipe_journal.views.web.ut.get_daily_random_sample")
    def test_recipe_ids_list_empty(self, mock_get_daily_random_sample):
        mock_get_daily_random_sample.return_value = []
        response = self.client.get(reverse("welcome"))

        self.assertEqual(response.status_code, 200)

class AddRecipeViewTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password"))
        self.member.save()
    
    def test_add_recipe_user_not_logged(self):
        response = self.client.post(reverse("add_recipe"))

        self.assertEqual(response.status_code, 302)

        # redirect_url = response["Location"]
        # self.assertEqual(redirect_url, "/login")
        self.assertRedirects(response, "/login")
    
    def test_add_recipe_form_unvalid(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        response = self.client.post(reverse("add_recipe"))

        self.assertEqual(response.status_code, 200)

    def test_add_recipe_success(self):
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


                                    