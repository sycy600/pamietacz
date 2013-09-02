from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.http import (HttpResponseRedirect,
                         HttpResponseNotFound,
                         HttpResponseBadRequest)
from django.test import TestCase
from pamietacz.models import Shelf, Deck, Card
from test_utils import (add_shelf,
                        add_deck,
                        add_card,
                        TestCaseWithAuthentication)
from PIL import Image
import StringIO
import shutil
import os


class AddCardTests(TestCaseWithAuthentication):
    def test_add_card(self):
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        card_question = "What is it?"
        card_answer = "This is that."

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)

        # There is no card shown on deck page.
        deck = Deck.objects.all()[0]
        r = self.client.get("/deck/%s/show/" % deck.id)
        self.assertNotIn(card_question, r.content)
        self.assertNotIn(card_answer, r.content)

        # There are now no cards in database.
        self.assertEqual(len(Card.objects.all()), 0)

        # Add new card.
        r = add_card(self.client, deck.id, card_question, card_answer)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # There is now one card in database.
        self.assertEqual(len(Card.objects.all()), 1)

        # Card is also shown on deck page.
        r = self.client.get("/deck/%s/show/" % deck.id)
        self.assertIn(card_question, r.content)
        self.assertIn(card_answer, r.content)

    def test_add_card_with_the_same_question_to_one_deck(self):
        """For one deck card questions must be unique. However
        different decks can have cards with the same questions."""
        shelf_name = "Some nice shelf"
        deck_name1 = "Some nice deck"
        deck_name2 = "Some other deck"
        card_question = "What is it?"
        card_answer = "This is that."

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name1)

        # Add some card.
        deck1 = Deck.objects.all()[0]
        add_card(self.client, deck1.id, card_question, card_answer)
        self.assertEqual(len(Card.objects.all()), 1)

        # Try to add another card with the same question to the same deck.
        # It is forbidden.
        r = add_card(self.client, deck1.id, card_question, card_answer)
        self.assertIn(("The question for this card already exists"
                       " in this deck."),
                      r.content)
        self.assertEqual(len(Card.objects.all()), 1)

        # Try to add another card with similar question but with
        # some trailing whitespaces. Question will be stripped
        # and the card will be not added.
        r = add_card(self.client, deck1.id, " What is it?    \n ",
                     card_answer)
        self.assertIn(("The question for this card already exists"
                       " in this deck."),
                      r.content)
        self.assertEqual(len(Card.objects.all()), 1)

        # Try to edit the same card without changing question.
        # It should pass - there is still only one card in the deck
        # with this question.
        cards = Card.objects.all()
        card = cards[0]
        r = self.client.post("/card/%s/edit/" % card.id,
                             {"question": card_question,
                              "answer": card_answer}, follow=True)
        self.assertNotIn(("The question for this card already exists"
                          " in this deck."),
                         r.content)

        # Add some another card successfully.
        add_card(self.client, deck1.id, "Yeyeye", card_answer)
        self.assertEqual(len(Card.objects.all()), 2)

        # Try to edit previous card with the question the same like
        # in new card just added - it should fail.
        r = self.client.post("/card/%s/edit/" % card.id,
                             {"question": "Yeyeye",
                              "answer": card_answer})
        self.assertIn(("The question for this card already exists"
                       " in this deck."),
                      r.content)

        # Add another deck.
        add_deck(self.client, shelf.id, deck_name2)
        deck2 = Deck.objects.all()[1]

        # Try to add new card with the same question like in previous card
        # but previous card was added to DIFFERENT deck. It should
        # be ok.
        r = add_card(self.client, deck2.id, card_question, card_answer)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        self.assertEqual(len(Card.objects.all()), 3)

        # Two cards with the same pair question and answer should be not
        # placed in database.
        card = Card(question="What is it?",
                    answer="This is that.",
                    deck=deck1)
        self.assertRaises(IntegrityError, card.save)

    def test_add_card_with_empty_question(self):
        """Question and answer for the card cannot be empty."""

        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        card_question = ""
        card_answer = "This is that."

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)

        # Get deck.
        deck = Deck.objects.all()[0]

        # Add new card.
        r = add_card(self.client, deck.id, card_question, card_answer)
        self.assertIn("This field is required.", r.content)


class EditCardTests(TestCaseWithAuthentication):
    def test_edit_card(self):
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        card_question = "What is it?"
        card_answer = "This is that."
        new_card_question = "Why so?"
        new_card_answer = "No idea"

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)

        # Add card.
        deck = Deck.objects.all()[0]
        add_card(self.client, deck.id, card_question, card_answer)

        # Only this card is in database.
        cards = Card.objects.all()
        card = cards[0]
        self.assertEqual(len(cards), 1)

        # Check if card is shown on deck page.
        r = self.client.get("/deck/%s/show/" % deck.id)
        self.assertIn(card_question, r.content)
        self.assertIn(card_answer, r.content)

        # Edit card.
        r = self.client.post("/card/%s/edit/" % card.id,
                             {"question": new_card_question,
                              "answer": new_card_answer})
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # Edited card is shown on deck page.
        r = self.client.get("/deck/%s/show/" % deck.id)
        self.assertNotIn(card_question, r.content)
        self.assertNotIn(card_answer, r.content)
        self.assertIn(new_card_question, r.content)
        self.assertIn(new_card_answer, r.content)

        # The number of card objects should not change.
        self.assertEqual(len(Card.objects.all()), 1)

    def test_edit_not_existing_card(self):
        r = self.client.get("/card/%d/edit/" % 777)
        self.assertEqual(r.status_code, HttpResponseNotFound.status_code)


class DeleteCardTests(TestCaseWithAuthentication):
    def test_delete_card(self):
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        card_question = "What is it?"
        card_answer = "This is that."

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)

        # Add card.
        deck = Deck.objects.all()[0]
        add_card(self.client, deck.id, card_question, card_answer)

        # Only this card is placed in database.
        cards = Card.objects.all()
        card = cards[0]
        self.assertEqual(len(cards), 1)

        # Check if card is shown on deck page.
        r = self.client.get("/deck/%s/show/" % deck.id)
        self.assertIn(card_question, r.content)
        self.assertIn(card_answer, r.content)

        # Delete card.
        r = self.client.get("/card/%s/delete/" % card.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # Card is not visible on deck page.
        r = self.client.get("/deck/%s/show/" % deck.id)
        self.assertNotIn(card_question, r.content)
        self.assertNotIn(card_answer, r.content)

        # There are also no cards in database.
        self.assertEqual(len(Card.objects.all()), 0)

    def test_delete_not_existing_card(self):
        r = self.client.get("/card/%d/delete/" % 777)
        self.assertEqual(r.status_code, HttpResponseNotFound.status_code)


class MarkdownCardTests(TestCaseWithAuthentication):
    def test_question_and_answer_use_markdown(self):
        """Markdown is used to make text looking nicer."""
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        card_question = "**What is it?**"
        card_answer = ("~~~~{.python}\n"
                       "import os\n"
                       "~~~~")

        # Add shelf, deck and card.
        add_shelf(self.client, shelf_name)
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)
        deck = Deck.objects.all()[0]
        add_card(self.client, deck.id, card_question, card_answer)

        # Text is processed by Markdown - ** is transformed to strong and
        # code listing is appropriately formatted.
        r = self.client.get("/deck/%s/show/" % deck.id)
        self.assertIn("<strong>What is it?</strong>", r.content)
        self.assertIn('<div class="codehilite"><pre><span class="kn">'
                      'import</span> <span class="nn">os</span>\n</pre>'
                      '</div>', r.content)


class NotAuthenticatedCardTests(TestCase):
    def test_add_card(self):
        self.assertEqual(len(Card.objects.all()), 0)
        r = add_card(self.client, 777, "Some question", "Some answer")
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        self.assertIn("login", r.get("location"))
        self.assertEqual(len(Card.objects.all()), 0)

    def test_edit_card(self):
        r = self.client.post("/card/%s/edit/" % 777,
                             {"name": "New card name"})
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        self.assertIn("login", r.get("location"))

    def test_delete_card(self):
        r = self.client.get("/card/%d/delete/" % 777)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)
        self.assertIn("login", r.get("location"))


class UploadImageTests(TestCaseWithAuthentication):
    def setUp(self):
        super(UploadImageTests, self).setUp()
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

    def tearDown(self):
        super(UploadImageTests, self).tearDown()
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

    def test_upload_image(self):
        # Create image.
        new_image = Image.new("RGB", (10, 10), (255, 255, 255))
        image_data = StringIO.StringIO()
        new_image.save(image_data, format="PNG")
        sent_file = SimpleUploadedFile("image_file.png",
                                       image_data.getvalue())

        # Check if image already doesn't exist.
        self.assertFalse(os.path.isfile(os.path.join(settings.MEDIA_ROOT,
                                                     "image_file.png")))

        # Upload image.
        r = self.client.post("/image/upload/", {"uploaded_image": sent_file})
        self.assertEqual(r.status_code, 200)

        # The name of image is returned in response.
        self.assertEqual(r.content, "image_file.png")

        # Check if now image exists.
        self.assertTrue(os.path.isfile(os.path.join(settings.MEDIA_ROOT,
                                                    "image_file.png")))

    def test_upload_file_which_is_not_image(self):
        """Only images can be uploaded. Other file types are discarded."""
        sent_file = SimpleUploadedFile("image_file.txt", "some text")
        self.assertFalse(os.path.isfile(os.path.join(settings.MEDIA_ROOT,
                                                     "image_file.png")))
        r = self.client.post("/image/upload/", {"uploaded_image": sent_file})

        # 400 error is returned when some other filetype than
        # image is uploaded.
        self.assertEqual(r.status_code, HttpResponseBadRequest.status_code)
        self.assertEqual(r.content, "")
        self.assertFalse(os.path.isfile(os.path.join(settings.MEDIA_ROOT,
                                                     "image_file.png")))

    def test_upload_file_with_the_same_name(self):
        """When uploaded file already exists, then Django takes care by
        adding appropriate suffix to make image name unique."""

        # Create image.
        new_image = Image.new("RGB", (10, 10), (255, 255, 255))
        image_data = StringIO.StringIO()
        new_image.save(image_data, format="PNG")
        first_image = SimpleUploadedFile("image_file.png",
                                         image_data.getvalue())

        # Upload first image.
        self.assertFalse(os.path.isfile(os.path.join(settings.MEDIA_ROOT,
                                                     "image_file.png")))
        r = self.client.post("/image/upload/",
                             {"uploaded_image": first_image})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, "image_file.png")
        self.assertTrue(os.path.isfile(os.path.join(settings.MEDIA_ROOT,
                                                    "image_file.png")))

        # Upload second image with the same name.
        second_image = SimpleUploadedFile("image_file.png",
                                          image_data.getvalue())
        r = self.client.post("/image/upload/",
                             {"uploaded_image": second_image})
        self.assertEqual(r.status_code, 200)

        # Suffix _1 is added to file name.
        self.assertEqual(r.content, "image_file_1.png")
        self.assertTrue(os.path.isfile(os.path.join(settings.MEDIA_ROOT,
                                                    "image_file_1.png")))
