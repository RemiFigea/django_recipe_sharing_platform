"""
Unit tests for the functions contained in the module utils.py.
"""
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from recipe_journal.models import Member, Recipe
import recipe_journal.utils.utils as ut
from django.urls import reverse
from unittest.mock import patch

class GetLoggedUserTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", password=make_password("password"))
        self.member.save()

    def test_get_logged_user_valid(self):
        self.client.post(reverse("login"), {"username": "testuser", "password": "password"})
        response  = self.client.get(reverse("welcome"))
        logged_user = ut.get_logged_user(response.wsgi_request)
        self.assertIsNotNone(logged_user)
        self.assertEqual(logged_user.username, "testuser")
    
    def test_get_logged_user_no_user(self):
        response  = self.client.get(reverse("welcome"))
        logged_user = ut.get_logged_user(response.wsgi_request)
        
        self.assertIsNone(logged_user)

class GetDailyRandomSampleTest(TestCase):
    def test_get_daily_random_sample_stable(self):
        Recipe.objects.create(title="Recipe 1")
        Recipe.objects.create(title="Recipe 2")
  
        result_1 = ut.get_daily_random_sample(2)
        result_2 = ut.get_daily_random_sample(2)
        
        self.assertEqual(result_1, result_2)

    def test_get_daily_random_sample_empty_database(self):
        result = ut.get_daily_random_sample(5)
        
        self.assertEqual(result, [])

    def test_get_daily_random_sample_less_than_requested(self):
        Recipe.objects.create(title="Recipe 1")
        result = ut.get_daily_random_sample(5)

        self.assertEqual(len(result), 1)

    def test_get_daily_random_sample_empty_list(self):
        result = ut.get_daily_random_sample(2)

        self.assertEqual(result, [])

    def test_get_daily_random_sample_random_behavior(self):
        for ind in range(10):
            Recipe.objects.create(title=f"Recipe {ind}")
       
        result = ut.get_daily_random_sample(2)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(id in range(1, 11) for id in result)) 