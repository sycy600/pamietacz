from django.http import (HttpResponseRedirect,
                         HttpResponseNotAllowed,
                         HttpResponseNotFound)
from django.test import TestCase
from pamietacz.models import Shelf
from test_utils import add_shelf, TestCaseWithAuthentication


class AddShelfTests(TestCaseWithAuthentication):
    def test_add_shelf(self):
        shelf_name = "Some nice shelf"
        r = self.client.get("/shelf/list/")
        self.assertNotIn(shelf_name, r.content)
        r = add_shelf(self.client, shelf_name)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        r = self.client.get("/shelf/list/")
        self.assertIn(shelf_name, r.content)
        self.assertEqual(len(Shelf.objects.all()), 1)

    def test_add_multiple_shelves(self):
        first_shelf_name = "First shelf name"
        second_shelf_name = "Second shelf name"
        r = self.client.get("/shelf/list/")
        self.assertNotIn(first_shelf_name, r.content)
        self.assertNotIn(second_shelf_name, r.content)
        r = add_shelf(self.client, first_shelf_name)
        r = add_shelf(self.client, second_shelf_name)
        r = self.client.get("/shelf/list/")
        self.assertIn(first_shelf_name, r.content)
        self.assertIn(second_shelf_name, r.content)

        # First shelf name is printed before second shelf name.
        first_shelf_name_index = r.content.find(first_shelf_name)
        second_shelf_name_index = r.content.find(second_shelf_name)
        self.assertLess(first_shelf_name_index, second_shelf_name_index)
        self.assertEqual(len(Shelf.objects.all()), 2)

    def test_add_shelf_with_already_existing_name(self):
        """It's forbidden to add new shelf with already existing name."""
        shelf_name = "Some nice shelf"
        r = self.client.get("/shelf/list/")
        self.assertNotIn(shelf_name, r.content)
        r = add_shelf(self.client, shelf_name)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        r = add_shelf(self.client, shelf_name)
        self.assertEqual(r.status_code, 200)
        self.assertIn("Shelf with this Name already exists.", r.content)
        r = self.client.get("/shelf/list/")
        # Some nice shelf name is placed only once in database.
        self.assertEqual(r.content.count(shelf_name), 1)
        self.assertEqual(len(Shelf.objects.all()), 1)

    def test_add_empty_shelf_name(self):
        """It's forbidden to add new shelf with an empty name."""
        shelf_name = ""
        r = add_shelf(self.client, shelf_name)
        self.assertEqual(r.status_code, 200)
        # This field is required. is displayed above name form field.
        self.assertIn("This field is required.", r.content)
        self.assertEqual(len(Shelf.objects.all()), 0)

    def test_use_not_allowed_method(self):
        """Only GET and POST methods are supported."""
        r = self.client.delete("/shelf/add/")
        self.assertEqual(r.status_code, HttpResponseNotAllowed.status_code)

    def test_add_blank_shelf_name(self):
        """It's forbidden to add new shelf with a blank name
        (for example only white spaces)."""
        shelf_name = " "
        r = add_shelf(self.client, shelf_name)
        self.assertEqual(r.status_code, 200)
        self.assertIn("This value cannot be whitespace only.", r.content)
        self.assertEqual(len(Shelf.objects.all()), 0)

    def test_add_shelf_name_longer_than_128_characters(self):
        """It's forbidden to add new shelf with name longer
        than 128 characters."""
        shelf_name = "a" * 129
        r = add_shelf(self.client, shelf_name)
        self.assertEqual(r.status_code, 200)
        self.assertIn("Ensure this value has at most 128"
                      " characters (it has 129).", r.content)
        self.assertEqual(len(Shelf.objects.all()), 0)

    def test_add_shelf_name_with_whitespace_around(self):
        """Whitespace characters are trimmed from shelf name."""
        shelf_name = "  Some shelf name  \t  "
        r = add_shelf(self.client, shelf_name)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        shelf_objects = Shelf.objects.all()
        self.assertEqual(len(shelf_objects), 1)
        self.assertEqual("Some shelf name", shelf_objects[0].name)


class EditShelfTests(TestCaseWithAuthentication):
    def test_edit_shelf(self):
        shelf_name = "Some nice shelf"
        shelf_new_name = "New name for shelf"

        add_shelf(self.client, shelf_name)

        # Shelf is shown on main page.
        r = self.client.get("/shelf/list/")
        self.assertIn(shelf_name, r.content)
        self.assertNotIn(shelf_new_name, r.content)

        # There is one shelf in database.
        shelf_objects = Shelf.objects.all()
        self.assertEqual(len(shelf_objects), 1)
        shelf_id = shelf_objects[0].id

        # Edit shelf.
        r = self.client.post("/shelf/%d/edit/" % shelf_id,
                             {"name": shelf_new_name})
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # Edited shelf is shown on main page.
        r = self.client.get("/shelf/list/")
        self.assertNotIn(shelf_name, r.content)
        self.assertIn(shelf_new_name, r.content)

        # There is still one shelf in database.
        self.assertEqual(len(Shelf.objects.all()), 1)

    def test_edit_not_existing_shelf(self):
        r = self.client.get("/shelf/%d/edit/" % 777)
        self.assertEqual(r.status_code, HttpResponseNotFound.status_code)
        r = self.client.post("/shelf/%d/edit/" % 777)
        self.assertEqual(r.status_code, HttpResponseNotFound.status_code)


class DeleteShelfTests(TestCaseWithAuthentication):
    def test_delete_shelf(self):
        shelf_name = "Some nice shelf"

        add_shelf(self.client, shelf_name)

        # Check if shelf is present on main page.
        r = self.client.get("/shelf/list/")
        self.assertIn(shelf_name, r.content)

        # Only this shelf is placed in database.
        shelf_objects = Shelf.objects.all()
        self.assertEqual(len(shelf_objects), 1)

        # Delete shelf.
        shelf_id = shelf_objects[0].id
        r = self.client.get("/shelf/%d/delete/" % shelf_id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # This shelf is now not shown on main page.
        r = self.client.get("/")
        self.assertNotIn(shelf_name, r.content)

        # There are now no shelves in database.
        self.assertEqual(len(Shelf.objects.all()), 0)

    def test_delete_not_existing_shelf(self):
        r = self.client.get("/shelf/%d/delete/" % 777)
        self.assertEqual(r.status_code, HttpResponseNotFound.status_code)


class NotAuthenticatedShelfTests(TestCase):
    def test_add_shelf(self):
        self.assertEqual(len(Shelf.objects.all()), 0)
        r = add_shelf(self.client, "Some Shelf")
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        self.assertIn("login", r.get("location"))
        self.assertEqual(len(Shelf.objects.all()), 0)

    def test_edit_shelf(self):
        r = self.client.post("/shelf/%s/edit/" % 777,
                             {"name": "New deck name"})
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        self.assertIn("login", r.get("location"))

    def test_delete_shelf(self):
        r = self.client.get("/shelf/%d/delete/" % 777)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        self.assertIn("login", r.get("location"))
