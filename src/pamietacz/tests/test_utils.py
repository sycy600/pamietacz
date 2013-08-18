from django.test import TestCase
from django.contrib.auth.models import User


def add_shelf(client, shelf_name):
    r = client.post("/shelf/add/", {"name": shelf_name})
    return r


def add_deck(client, shelf_id, deck_name):
    r = client.post("/shelf/%s/deck/add/" % shelf_id,
                    {"name": deck_name})
    return r


def add_card(client, deck_id, question, answer):
    r = client.post("/deck/%s/card/add/" % deck_id,
                    {"question": question,
                     "answer": answer})
    return r


class TestCaseWithAuthentication(TestCase):
    def setUp(self):
        username = "John"
        password = "some_password"
        User.objects.create_user(username=username, password=password)
        self.client.login(username=username, password=password)

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()
