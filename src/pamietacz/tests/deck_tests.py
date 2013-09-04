from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.test import TestCase
from pamietacz.models import Shelf, Deck
from test_utils import (add_shelf,
                        add_deck,
                        add_card,
                        TestCaseWithAuthentication)


class AddDeckTests(TestCaseWithAuthentication):
    def test_add_deck(self):
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"

        add_shelf(self.client, shelf_name)

        # Deck is not shown on shelf page.
        shelf = Shelf.objects.all()[0]
        r = self.client.get("/shelf/%s/show/" % shelf.id)
        self.assertNotIn(deck_name, r.content)

        # Add deck.
        r = add_deck(self.client, shelf.id, deck_name)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # There is one deck in database.
        self.assertEqual(len(Deck.objects.all()), 1)

        # Shelf is assigned to the deck.
        deck = Deck.objects.all()[0]
        self.assertEqual(deck.shelf.id, shelf.id)
        self.assertEqual(deck.name, deck_name)

        # First deck has order 0 which means that it's first.
        self.assertEqual(deck.order, 0)

        # Deck is shown on shelf page.
        r = self.client.get("/shelf/%s/show/" % shelf.id)
        self.assertIn(deck_name, r.content)


class EditDeckTests(TestCaseWithAuthentication):
    def test_edit_deck(self):
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        new_deck_name = "New deck name"

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)

        # There is one deck in database.
        self.assertEqual(len(Deck.objects.all()), 1)

        # Deck is shown on shelf page.
        r = self.client.get("/shelf/%s/show/" % shelf.id)
        self.assertIn(deck_name, r.content)

        # Edit deck.
        deck = Deck.objects.all()[0]
        remember_deck_id = deck.id
        r = self.client.post("/deck/%s/edit/" % deck.id,
                             {"name": new_deck_name})
        deck = Deck.objects.all()[0]

        # Id of edited deck has not changed.
        self.assertEqual(remember_deck_id, deck.id)

        # Edited deck is shown on shelf page.
        r = self.client.get("/shelf/%s/show/" % shelf.id)
        self.assertNotIn(deck_name, r.content)
        self.assertIn(new_deck_name, r.content)

        # The number of decks is still one in database.
        self.assertEqual(len(Deck.objects.all()), 1)

    def test_edit_not_existing_deck(self):
        r = self.client.post("/deck/%s/edit/" % 777)
        self.assertEqual(r.status_code, HttpResponseNotFound.status_code)


class DeleteDeckTests(TestCaseWithAuthentication):
    def test_delete_deck(self):
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        r = add_deck(self.client, shelf.id, deck_name)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # There is now one deck in database.
        self.assertEqual(len(Deck.objects.all()), 1)

        # The deck is shown on shelf page.
        r = self.client.get("/shelf/%s/show/" % shelf.id)
        self.assertIn(deck_name, r.content)

        # Delete deck.
        deck = Deck.objects.all()[0]
        r = self.client.get("/deck/%s/delete/" % deck.id)

        # The deck is now not shown on shelf page.
        r = self.client.get("/shelf/%s/show/" % shelf.id)
        self.assertNotIn(deck_name, r.content)

        # There are now no decks in database.
        self.assertEqual(len(Deck.objects.all()), 0)

    def test_delete_not_existing_shelf(self):
        r = self.client.get("/deck/%d/delete/" % 777)
        self.assertEqual(r.status_code, HttpResponseNotFound.status_code)


class CountCardsOfDeckTests(TestCaseWithAuthentication):
    def test_count_cards_of_deck_tests(self):
        """User can see on deck page how many cards
        are placed in specific deck."""
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        card_question = "Is?"
        card_answer = "Yes"

        # Add shelf, deck and card.
        add_shelf(self.client, shelf_name)
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)
        deck = Deck.objects.all()[0]

        # There are no cards in deck yet.
        r = self.client.get("/shelf/%s/show/" % shelf.id)
        self.assertIn("(0)", r.content)

        # Now there card is added.
        add_card(self.client, deck.id, card_question, card_answer)

        # There is one card in deck.
        r = self.client.get("/shelf/%s/show/" % shelf.id)
        self.assertNotIn("(0)", r.content)
        self.assertIn("(1)", r.content)


class NotAuthenticatedDeckTests(TestCase):
    def test_add_deck(self):
        self.assertEqual(len(Deck.objects.all()), 0)
        r = add_deck(self.client, 777, "Some Deck")
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        self.assertIn("login", r.get("location"))
        self.assertEqual(len(Deck.objects.all()), 0)

    def test_edit_deck(self):
        r = self.client.post("/deck/%s/edit/" % 777,
                             {"name": "New deck name"})
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        self.assertIn("login", r.get("location"))

    def test_delete_deck(self):
        r = self.client.get("/deck/%d/delete/" % 777)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        self.assertIn("login", r.get("location"))


class MovingDecks(TestCaseWithAuthentication):
    def test_add_multiple_decks_and_check_order(self):
        shelf_name = "Some nice shelf"
        first_deck_name = "First deck"
        second_deck_name = "Second deck"
        third_deck_name = "Third deck"

        add_shelf(self.client, shelf_name)

        # Add decks.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, first_deck_name)
        add_deck(self.client, shelf.id, second_deck_name)
        add_deck(self.client, shelf.id, third_deck_name)

        all_decks = Deck.objects.all()
        # Each new added deck has order so it's maximum value
        # of other orders + 1
        self.assertEqual(all_decks[0].order, 0)
        self.assertEqual(all_decks[1].order, 1)
        self.assertEqual(all_decks[2].order, 2)

    def test_delete_decks_and_check_order(self):
        shelf_name = "Some nice shelf"
        first_deck_name = "First deck"
        second_deck_name = "Second deck"
        third_deck_name = "Third deck"

        add_shelf(self.client, shelf_name)

        # Add decks.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, first_deck_name)
        add_deck(self.client, shelf.id, second_deck_name)
        add_deck(self.client, shelf.id, third_deck_name)

        all_decks = Deck.objects.all()

        self.assertEqual(len(all_decks), 3)

        # Delete deck in the middle.
        self.client.get("/deck/%d/delete/" % all_decks[1].id)

        all_decks = Deck.objects.all()

        # Order of last deck (third deck) was decreased in order
        # to achieve continuity.
        self.assertEqual(len(all_decks), 2)
        self.assertEqual(all_decks[0].order, 0)
        self.assertEqual(all_decks[0].name, first_deck_name)
        self.assertEqual(all_decks[1].order, 1)
        self.assertEqual(all_decks[1].name, third_deck_name)

    def test_move_deck_up(self):
        shelf_name = "Some nice shelf"
        first_deck_name = "First deck"
        second_deck_name = "Second deck"
        third_deck_name = "Third deck"

        add_shelf(self.client, shelf_name)

        # Add decks.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, first_deck_name)
        add_deck(self.client, shelf.id, second_deck_name)
        add_deck(self.client, shelf.id, third_deck_name)

        all_decks = Deck.objects.all()

        # Initial orders:
        # 0 first deck
        # 1 second deck
        # 2 third deck
        self.assertEqual(all_decks[0].order, 0)
        self.assertEqual(all_decks[0].name, first_deck_name)
        self.assertEqual(all_decks[1].order, 1)
        self.assertEqual(all_decks[1].name, second_deck_name)
        self.assertEqual(all_decks[2].order, 2)
        self.assertEqual(all_decks[2].name, third_deck_name)

        self.client.get("/deck/%d/move/up/" % all_decks[0].id)

        all_decks = Deck.objects.all()

        # Move first deck up:
        # 0 second deck
        # 1 first deck
        # 2 third deck
        self.assertEqual(all_decks[0].order, 1)
        self.assertEqual(all_decks[0].name, first_deck_name)
        self.assertEqual(all_decks[1].order, 0)
        self.assertEqual(all_decks[1].name, second_deck_name)
        self.assertEqual(all_decks[2].order, 2)
        self.assertEqual(all_decks[2].name, third_deck_name)

        self.client.get("/deck/%d/move/up/" % all_decks[0].id)

        all_decks = Deck.objects.all()

        # Move first deck up:
        # 0 second deck
        # 1 third deck
        # 2 first deck
        self.assertEqual(all_decks[0].order, 2)
        self.assertEqual(all_decks[0].name, first_deck_name)
        self.assertEqual(all_decks[1].order, 0)
        self.assertEqual(all_decks[1].name, second_deck_name)
        self.assertEqual(all_decks[2].order, 1)
        self.assertEqual(all_decks[2].name, third_deck_name)

        self.client.get("/deck/%d/move/up/" % all_decks[0].id)

        all_decks = Deck.objects.all()

        # Move first deck up (nothing will change because it's already
        # on top):
        # 0 second deck
        # 1 third deck
        # 2 first deck
        self.assertEqual(all_decks[0].order, 2)
        self.assertEqual(all_decks[0].name, first_deck_name)
        self.assertEqual(all_decks[1].order, 0)
        self.assertEqual(all_decks[1].name, second_deck_name)
        self.assertEqual(all_decks[2].order, 1)
        self.assertEqual(all_decks[2].name, third_deck_name)

    def test_move_deck_down(self):
        shelf_name = "Some nice shelf"
        first_deck_name = "First deck"
        second_deck_name = "Second deck"
        third_deck_name = "Third deck"

        add_shelf(self.client, shelf_name)

        # Add decks.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, first_deck_name)
        add_deck(self.client, shelf.id, second_deck_name)
        add_deck(self.client, shelf.id, third_deck_name)

        all_decks = Deck.objects.all()

        # Initial orders:
        # 0 first deck
        # 1 second deck
        # 2 third deck
        self.assertEqual(all_decks[0].order, 0)
        self.assertEqual(all_decks[0].name, first_deck_name)
        self.assertEqual(all_decks[1].order, 1)
        self.assertEqual(all_decks[1].name, second_deck_name)
        self.assertEqual(all_decks[2].order, 2)
        self.assertEqual(all_decks[2].name, third_deck_name)

        self.client.get("/deck/%d/move/down/" % all_decks[2].id)

        all_decks = Deck.objects.all()

        # Move third deck down:
        # 0 first deck
        # 1 third deck
        # 2 second deck
        self.assertEqual(all_decks[0].order, 0)
        self.assertEqual(all_decks[0].name, first_deck_name)
        self.assertEqual(all_decks[1].order, 2)
        self.assertEqual(all_decks[1].name, second_deck_name)
        self.assertEqual(all_decks[2].order, 1)
        self.assertEqual(all_decks[2].name, third_deck_name)

        self.client.get("/deck/%d/move/down/" % all_decks[2].id)

        all_decks = Deck.objects.all()

        # Move third deck down:
        # 0 third deck
        # 1 first deck
        # 2 second deck
        self.assertEqual(all_decks[0].order, 1)
        self.assertEqual(all_decks[0].name, first_deck_name)
        self.assertEqual(all_decks[1].order, 2)
        self.assertEqual(all_decks[1].name, second_deck_name)
        self.assertEqual(all_decks[2].order, 0)
        self.assertEqual(all_decks[2].name, third_deck_name)

        self.client.get("/deck/%d/move/down/" % all_decks[2].id)

        all_decks = Deck.objects.all()

        # Move third deck down (nothing will change because it's already
        # on bottom):
        # 0 third deck
        # 1 first deck
        # 2 second deck
        self.assertEqual(all_decks[0].order, 1)
        self.assertEqual(all_decks[0].name, first_deck_name)
        self.assertEqual(all_decks[1].order, 2)
        self.assertEqual(all_decks[1].name, second_deck_name)
        self.assertEqual(all_decks[2].order, 0)
        self.assertEqual(all_decks[2].name, third_deck_name)
