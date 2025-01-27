"""
Unit tests for the functions of the RecipeActionForm in the forms module.

Tests included:
    - test_form_checkboxes: Verifies the form's checkbox inputs and their cleaned data.
"""
from django.test import TestCase
from recipe_journal.forms import RecipeActionForm

class RecipeActionFormTest(TestCase):

    def test_form_checkboxes(self):
        form_data = {
            "add_to_history": True,
            "add_to_album": False,
            "add_to_recipe_to_try": True,
        }
        form = RecipeActionForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["add_to_history"], True)
        self.assertEqual(form.cleaned_data["add_to_album"], False)
        self.assertEqual(form.cleaned_data["add_to_recipe_to_try"], True)