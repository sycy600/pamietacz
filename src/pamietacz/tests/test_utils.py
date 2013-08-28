from django.test import TestCase, TransactionTestCase
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


def create_and_login_default_user(client):
    username = "John"
    password = "some_password"
    User.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)


def logout_and_delete_user(client):
    client.logout()
    User.objects.all().delete()


class TestCaseWithAuthentication(TestCase):
    def setUp(self):
        create_and_login_default_user(self.client)

    def tearDown(self):
        logout_and_delete_user(self.client)


class TransactionTestCaseWithAuthentication(TransactionTestCase):
    def setUp(self):
        create_and_login_default_user(self.client)

    def tearDown(self):
        logout_and_delete_user(self.client)
