from django.contrib.auth.hashers import make_password
from django.test import TestCase, TransactionTestCase
from pamietacz.models import UserProfile


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


username = "John"
password = "some_password"
# It looks like that creating of password hash can take several
# seconds for all tests so it's faster to do it once outside
# test setup method.
hashed_password = make_password(password)


def create_and_login_default_user(client):
    user = UserProfile(username=username, password=hashed_password)
    user.save()
    client.login(username=username, password=password)


def logout_and_delete_user(client):
    client.logout()
    UserProfile.objects.all().delete()


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
