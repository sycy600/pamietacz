from django.conf import settings
from django.db import IntegrityError, transaction
from datetime import datetime
import os
import shutil
from models import Shelf, Deck, Card
from lxml import etree


def backup_db():
    if not settings.DEBUG:
        return
    now = datetime.now()
    formatted_date = now.strftime("%Y_%m_%d_%H_%M_%S_%f")
    database_name = settings.DATABASES["default"]["NAME"]
    backup_directory = "backups"
    if not os.path.isdir(backup_directory):
        os.mkdir(backup_directory)
    backup_file_name = os.path.join(backup_directory,
                                    database_name + "_" + formatted_date)
    shutil.copy(database_name, backup_file_name)


def backup(function):
    def wrap(request, *args, **kwargs):
        backup_db()
        return function(request, *args, **kwargs)
    return wrap


def dump_data_as_xml():
    root = etree.Element("data")
    all_shelves = Shelf.objects.all()
    for shelf in all_shelves:
        shelf_xml = etree.Element("shelf")
        shelf_xml.attrib["name"] = shelf.name
        root.append(shelf_xml)
        decks = Deck.objects.filter(shelf=shelf)
        for deck in decks:
            deck_xml = etree.Element("deck")
            deck_xml.attrib["name"] = deck.name
            shelf_xml.append(deck_xml)
            cards = Card.objects.filter(deck=deck).order_by("id")
            for card in cards:
                card_xml = etree.Element("card")
                card_question_xml = etree.Element("question")
                card_question_xml.text = card.question
                card_xml.append(card_question_xml)
                card_answer_xml = etree.Element("answer")
                card_answer_xml.text = card.answer
                card_xml.append(card_answer_xml)
                deck_xml.append(card_xml)
    return etree.tostring(root,
                          xml_declaration=True,
                          encoding="UTF-8",
                          pretty_print=True)


class XMLDataDumpException(Exception):
    pass


@transaction.commit_on_success
def load_data_as_xml(data_dump_as_xml):
    tree = etree.parse(data_dump_as_xml)
    docinfo = tree.docinfo
    if docinfo.encoding != "UTF-8":
        raise XMLDataDumpException("Not supported encoding: %s" %
                                   docinfo.encoding)
    root = tree.getroot()
    if root.tag != "data":
        raise XMLDataDumpException("%s: %s != 'data'" %
                                   (root.sourceline, root.tag))
    for shelf_xml in root:
        if shelf_xml.tag != "shelf":
            raise XMLDataDumpException("%s: %s != 'shelf'" %
                                       (shelf_xml.sourceline, shelf_xml.tag))
        shelf = Shelf()
        shelf.name = shelf_xml.get("name")
        try:
            shelf.save()
        except IntegrityError as e:
            raise XMLDataDumpException("%s: cannot add shelf: %s" %
                                       (shelf_xml.sourceline, str(e)))
        for deck_data in shelf_xml:
            if deck_data.tag != "deck":
                raise XMLDataDumpException("%s: %s != 'deck'" %
                                           (deck_data.sourceline,
                                            deck_data.tag))
            deck = Deck()
            deck.shelf = shelf
            deck.name = deck_data.get("name")
            deck.save()
            for card_data in deck_data:
                if card_data.tag != "card":
                    raise XMLDataDumpException("%s: %s != 'card'" %
                                               (card_data.sourceline,
                                                card_data.tag))
                if card_data[0].tag != "question":
                    raise XMLDataDumpException("%s: %s != 'question'" %
                                               (card_data[0].sourceline,
                                                card_data[0].tag))
                if card_data[1].tag != "answer":
                    raise XMLDataDumpException("%s: s%s != 'answer'" %
                                               (card_data[1].sourceline,
                                                card_data[1].tag))
                card = Card()
                card.deck = deck
                card.question = card_data[0].text
                card.answer = card_data[1].text
                card.save()
