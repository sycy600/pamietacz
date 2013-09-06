from django.core.files.uploadedfile import SimpleUploadedFile
from pamietacz.models import Shelf, Deck, Card
from test_utils import (add_shelf,
                        add_deck,
                        add_card,
                        TransactionTestCaseWithAuthentication)


class DumpLoadTests(TransactionTestCaseWithAuthentication):
    def test_dump_and_load(self):
        # Add shelves.
        add_shelf(self.client, "1st shelf")
        add_shelf(self.client, "2nd shelf><\"&")
        add_shelf(self.client, "3rd shelf")

        # Add decks.
        all_shelves = Shelf.objects.all()
        first_shelf = all_shelves[0]
        add_deck(self.client, first_shelf.id, "1st shelf 1st deck><\"&")
        add_deck(self.client, first_shelf.id, "1st shelf 2nd deck")

        # Add some cards.
        all_decks = Deck.objects.all()
        first_shelf_first_deck = all_decks[0]
        add_card(self.client, first_shelf_first_deck.id,
                 "1st deck 1st question><",
                 "1st deck 1st answer><\"&")

        first_shelf_second_deck = all_decks[1]
        add_card(self.client, first_shelf_second_deck.id,
                 "2nd deck 1st question",
                 "2nd deck 1st answer")
        add_card(self.client, first_shelf_second_deck.id,
                 "2nd deck 2nd question",
                 "2nd deck 2nd answer")

        all_cards = Card.objects.all()

        # Check the number of added shelves, decks and cards.
        self.assertEqual(len(all_cards), 3)
        self.assertEqual(len(all_shelves), 3)
        self.assertEqual(len(all_decks), 2)

        # Remember shelves for next checks.
        first_shelf = all_shelves[0]
        second_shelf = all_shelves[1]
        third_shelf = all_shelves[2]

        # Remember decks for next checks.
        first_shelf_first_deck = all_decks[0]
        first_shelf_second_deck = all_decks[1]

        # Remember questions for next checks.
        first_deck_first_question = all_cards[0].question
        first_deck_first_answer = all_cards[0].answer
        second_deck_first_question = all_cards[1].question
        second_deck_first_answer = all_cards[1].answer
        second_deck_second_question = all_cards[2].question
        second_deck_second_answer = all_cards[2].answer

        # Check if correct XML file was generated.
        r = self.client.get("/data/dump/")
        c = ("""<?xml version='1.0' encoding='UTF-8'?>\n"""
             """<data>\n"""
             """  <shelf name="1st shelf">\n"""
             """    <deck name="1st shelf 1st deck&gt;&lt;&quot;&amp;">\n"""
             """      <card>\n"""
             """        <question>1st deck 1st question&gt;&lt;</question>\n"""
             """        <answer>1st deck 1st answer&gt;&lt;"&amp;</answer>\n"""
             """      </card>\n"""
             """    </deck>\n"""
             """    <deck name="1st shelf 2nd deck">\n"""
             """      <card>\n"""
             """        <question>2nd deck 1st question</question>\n"""
             """        <answer>2nd deck 1st answer</answer>\n"""
             """      </card>\n"""
             """      <card>\n"""
             """        <question>2nd deck 2nd question</question>\n"""
             """        <answer>2nd deck 2nd answer</answer>\n"""
             """      </card>\n"""
             """    </deck>\n"""
             """  </shelf>\n"""
             """  <shelf name="2nd shelf&gt;&lt;&quot;&amp;"/>\n"""
             """  <shelf name="3rd shelf"/>\n"""
             """</data>\n""")
        self.assertEqual(c, r.content)
        self.assertEqual(200, r.status_code)

        # Delete all shelves (with all decks and cards) from database.
        shelves = Shelf.objects.all()
        for shelf in shelves:
            self.client.get("/shelf/%d/delete/" % shelf.id)

        # Check if all cards were deleted.
        self.assertEqual(len(Card.objects.all()), 0)
        self.assertEqual(len(Shelf.objects.all()), 0)
        self.assertEqual(len(Deck.objects.all()), 0)

        # Load data from XML file back to database.
        sent_file = SimpleUploadedFile("dump_data.xml", r.content)
        r = self.client.post("/data/load/", {"data_dump_file": sent_file},
                             follow=True)
        self.assertEqual(200, r.status_code)

        all_shelves = Shelf.objects.all()
        all_decks = Deck.objects.all()
        all_cards = Card.objects.all()

        # Check number of loaded cards from file.
        self.assertEqual(len(all_cards), 3)
        self.assertEqual(len(all_shelves), 3)
        self.assertEqual(len(all_decks), 2)

        # Check if loaded shelves are the same as previously
        # located in database.
        self.assertEqual(first_shelf, all_shelves[0])
        self.assertEqual(second_shelf, all_shelves[1])
        self.assertEqual(third_shelf, all_shelves[2])

        # Check if loaded decks are the same as previously
        # located in database.
        self.assertEqual(first_shelf_first_deck, all_decks[0])
        self.assertEqual(first_shelf_second_deck, all_decks[1])

        # Check if loaded cards are the same as previously
        # located in database.
        self.assertEqual(first_deck_first_question,
                         all_cards[0].question)
        self.assertEqual(first_deck_first_answer,
                         all_cards[0].answer)
        self.assertEqual(second_deck_first_question,
                         all_cards[1].question)
        self.assertEqual(second_deck_first_answer,
                         all_cards[1].answer)
        self.assertEqual(second_deck_second_question,
                         all_cards[2].question)
        self.assertEqual(second_deck_second_answer,
                         all_cards[2].answer)

        # Check the structure.
        # first shelf first deck
        self.assertEqual(all_decks[0].shelf, all_shelves[0])

        # first shelf second deck
        self.assertEqual(all_decks[1].shelf, all_shelves[0])

        # first shelf first deck first card
        self.assertEqual(all_cards[0].deck, all_decks[0])

        # first shelf second deck first card
        self.assertEqual(all_cards[1].deck, all_decks[1])

        # first shelf second deck second card
        self.assertEqual(all_cards[2].deck, all_decks[1])

    def test_load_not_xml_file(self):
        """No XML files are allowed."""
        sent_file = SimpleUploadedFile("dump_data.xml", "dsfsdfsdfsd")
        r = self.client.post("/data/load/", {"data_dump_file": sent_file},
                             follow=True)
        self.assertEqual(200, r.status_code)
        self.assertIn("Error while parsing XML: Start tag expected",
                      r.content)
        self.assertEqual(len(Card.objects.all()), 0)
        self.assertEqual(len(Shelf.objects.all()), 0)
        self.assertEqual(len(Deck.objects.all()), 0)

    def test_load_wrong_encoding_unknown(self):
        """Unknown encoding provided."""
        xml_content = "<?xml version='1.0' encoding='aaa-8'?><shelf></shelf>"
        sent_file = SimpleUploadedFile("dump_data.xml", xml_content)
        r = self.client.post("/data/load/", {"data_dump_file": sent_file},
                             follow=True)
        self.assertEqual(200, r.status_code)
        self.assertIn("Error while parsing XML: Unsupported encoding aaa-8",
                      r.content)
        self.assertEqual(len(Card.objects.all()), 0)
        self.assertEqual(len(Shelf.objects.all()), 0)
        self.assertEqual(len(Deck.objects.all()), 0)

    def test_load_wrong_encoding_not_supported(self):
        """Not supported encoding provided."""
        xml_content = "<?xml version='1.0' encoding='ASCII'?><shelf></shelf>"
        sent_file = SimpleUploadedFile("dump_data.xml", xml_content)
        r = self.client.post("/data/load/", {"data_dump_file": sent_file},
                             follow=True)
        self.assertEqual(200, r.status_code)
        self.assertIn("Error while parsing XML: "
                      "Not supported encoding: ASCII",
                      r.content)
        self.assertEqual(len(Card.objects.all()), 0)
        self.assertEqual(len(Shelf.objects.all()), 0)
        self.assertEqual(len(Deck.objects.all()), 0)

    def test_load_wrong_root_element_name(self):
        """Root elements is called 'data' and other are refused."""
        sent_file = SimpleUploadedFile("dump_data.xml", "<shelllf></shelllf>")
        r = self.client.post("/data/load/", {"data_dump_file": sent_file},
                             follow=True)
        self.assertEqual(200, r.status_code)
        self.assertIn("Error while parsing XML: 1: shelllf != &#39;data&#39;",
                      r.content)
        self.assertEqual(len(Card.objects.all()), 0)
        self.assertEqual(len(Shelf.objects.all()), 0)
        self.assertEqual(len(Deck.objects.all()), 0)

    def test_no_name_for_shelf(self):
        """Shelf must have 'name' attribute."""
        sent_file = SimpleUploadedFile("dump_data.xml",
                                       "<data><shelf></shelf></data>")
        r = self.client.post("/data/load/", {"data_dump_file": sent_file},
                             follow=True)
        self.assertEqual(200, r.status_code)
        self.assertIn("Error while parsing XML: 1: cannot add shelf: "
                      "pamietacz_shelf.name may not be NULL", r.content)
        self.assertEqual(len(Card.objects.all()), 0)
        self.assertEqual(len(Shelf.objects.all()), 0)
        self.assertEqual(len(Deck.objects.all()), 0)

    def test_shelf_already_exists(self):
        """Shelf with the same name as one which already
        is present in database won't be added."""
        add_shelf(self.client, "aa")
        xml_content = "<data><shelf name=\"aa\"></shelf></data>"
        sent_file = SimpleUploadedFile("dump_data.xml", xml_content)
        r = self.client.post("/data/load/", {"data_dump_file": sent_file},
                             follow=True)
        self.assertEqual(200, r.status_code)
        self.assertIn("Error while parsing XML: 1: cannot add shelf: "
                      "column name is not unique", r.content)
        self.assertEqual(len(Card.objects.all()), 0)
        self.assertEqual(len(Shelf.objects.all()), 1)
        self.assertEqual(len(Deck.objects.all()), 0)

    def test_partially_wrong_xml_file(self):
        """If XML file is partially wrong then nothing
        won't be added at all."""
        xml_content = ("<data><shelf name=\"aa\"></shelf>"
                       "<shelf name=\"bb\"><deck name=\"xx\"><ee></ee></deck>"
                       "</shelf></data>")
        sent_file = SimpleUploadedFile("dump_data.xml", xml_content)
        r = self.client.post("/data/load/", {"data_dump_file": sent_file},
                             follow=True)
        self.assertEqual(200, r.status_code)
        self.assertIn("Error while parsing XML: 1: ee != &#39;card&#39;",
                      r.content)
        self.assertEqual(len(Card.objects.all()), 0)
        self.assertEqual(len(Shelf.objects.all()), 0)
        self.assertEqual(len(Deck.objects.all()), 0)

    def test_order_of_decks_is_taken_into_account(self):
        """Order of decks is kept in XML dump so that decks are sorted
        by order."""

        add_shelf(self.client, "first shelf")

        # Add decks.
        all_shelves = Shelf.objects.all()
        add_deck(self.client, all_shelves[0].id, "first deck")
        add_deck(self.client, all_shelves[0].id, "second deck")

        all_decks = Deck.objects.all()

        # Move first shelf up.
        self.client.get("/deck/%d/move/up/" % all_decks[0].id)

        # Second shelf is listed as first and first shelf is listed as second.
        r = self.client.get("/data/dump/")
        c = ("""<?xml version='1.0' encoding='UTF-8'?>\n"""
             """<data>\n"""
             """  <shelf name="first shelf">\n"""
             """    <deck name="second deck"/>\n"""
             """    <deck name="first deck"/>\n"""
             """  </shelf>\n"""
             """</data>\n""")
        self.assertEqual(c, r.content)
