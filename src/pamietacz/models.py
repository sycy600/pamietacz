from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models, transaction
import re
import random
import datetime
from markdown import Markdown


markdown_instance = Markdown(extensions=["tables",
                                         "fenced_code",
                                         "codehilite"],
                             output_format="html5")


def whitespace_validator(text):
    if re.match("^\s+$", text):
        raise ValidationError(u"This value cannot be whitespace only.")


class Shelf(models.Model):
    name = models.CharField(max_length=128,
                            unique=True,
                            blank=False,
                            validators=[whitespace_validator])

    def clean(self):
        self.name = self.name.strip()


class Deck(models.Model):
    name = models.CharField(max_length=128,
                            blank=False,
                            validators=[whitespace_validator])
    order = models.PositiveIntegerField(blank=False)
    shelf = models.ForeignKey(Shelf)

    def clean(self):
        self.name = self.name.strip()

    def delete(self):
        decks_to_update = Deck.objects.filter(shelf=self.shelf,
                                              order__gt=self.order)
        decks_to_update.update(order=models.F("order") - 1)
        super(Deck, self).delete()

    @transaction.commit_on_success
    def move(self, direction):
        try:
            if direction == "up":
                order = self.order + 1
            elif direction == "down":
                order = self.order - 1
            else:
                raise ValueError("Unknown order: %s" % order)
            deck_nearby = Deck.objects.get(shelf=self.shelf, order=order)
            deck_nearby.order, self.order = self.order, deck_nearby.order
            self.save()
            deck_nearby.save()
        except Deck.DoesNotExist:
            pass

    def save(self, *args, **kwargs):
        if self.pk is None:
            if Deck.objects.filter(shelf=self.shelf).count() == 0:
                self.order = 0
            else:
                decks_to_search = Deck.objects.filter(shelf=self.shelf)
                max_query = decks_to_search.aggregate(models.Max("order"))
                self.order = max_query["order__max"] + 1
        super(Deck, self).save(*args, **kwargs)


class Card(models.Model):
    question = models.TextField(blank=False,
                                validators=[whitespace_validator])
    answer = models.TextField(blank=False,
                              validators=[whitespace_validator])
    question_after_markdown = (
        models.TextField(blank=False, validators=[whitespace_validator]))
    answer_after_markdown = (
        models.TextField(blank=False, validators=[whitespace_validator]))
    deck = models.ForeignKey(Deck)

    class Meta:
        unique_together = ("deck", "question")

    def save(self, *args, **kwargs):
        self.answer_after_markdown = markdown_instance.convert(self.answer)
        self.question_after_markdown = markdown_instance.convert(self.question)
        super(Card, self).save(*args, **kwargs)


class UserProfile(AbstractUser):
    shelves = models.ManyToManyField(Shelf)

    objects = UserManager()

    def started_shelf(self, shelf):
        return shelf in self.shelves.all()


class TrainCard(models.Model):
    """Train card remembers state of given card for specific user."""
    card = models.ForeignKey(Card)
    time_to_show = models.DateTimeField(auto_now_add=True)
    i = models.IntegerField(default=0)
    ef = models.FloatField(default=2.5)
    n = models.IntegerField(default=0)

    def _calculate_new_ef(self, q):
        new_ef = self.ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        if new_ef < 1.3:
            new_ef = 1.3
        self.ef = new_ef

    def calculate_interval(self, q):
        """SuperMemo 2 algorithm (slightly modified)."""

        # Calculate new EF only for good answers.
        if not q < 3:
            self._calculate_new_ef(q)
            self.n += 1
            if self.n == 1:
                self.i = 1
            elif self.n == 2:
                self.i = 6
            else:
                self.i = self.i * self.ef
        else:
            # If answer was wrong then make it so reset counter of answers for
            # this question. However old EF is kept.
            self.n = 0

        # Set new time to show only for good answers.
        if not q < 4:
            self.time_to_show = (
                datetime.datetime.now() +
                datetime.timedelta(seconds=int(24 * 60 * self.i)))


class TrainPool(models.Model):
    """Train pool is source of cards for specific user. When new session
    starts then the cards are retrieved from this pool."""
    deck = models.ForeignKey(Deck)
    userprofile = models.ForeignKey(UserProfile)
    train_cards = models.ManyToManyField(TrainCard)

    @classmethod
    def create_or_get_train_pool(cls, userprofile, deck):
        try:
            train_pool = TrainPool.objects.get(userprofile=userprofile,
                                               deck=deck)
        except TrainPool.DoesNotExist:
            train_pool = cls.create_train_pool(userprofile, deck)
        return train_pool

    @classmethod
    def create_train_pool(cls, userprofile, deck):
        cards = Card.objects.filter(deck=deck)
        train_pool = TrainPool(userprofile=userprofile, deck=deck)
        train_pool.save()

        # Fill pool with cards.
        for card in cards:
            train_card = TrainCard(card=card)
            train_card.save()
            train_pool.train_cards.add(train_card)
        train_pool.save()
        return train_pool

    def number_of_cards_to_repeat_now(self):
        items = 0
        for train_card in self.train_cards.all():
            if train_card.time_to_show <= datetime.datetime.now():
                items += 1
        return items


class TrainSession(models.Model):
    """When user starts to train specific deck, then there is created
    a session for this training. Session retrieves cards from training
    pool. Session lives until user won't answer all questions from card.
    Then session is killed."""
    deck = models.ForeignKey(Deck)
    userprofile = models.ForeignKey(UserProfile)

    # Training cards used in given session.
    train_cards = models.CommaSeparatedIntegerField(max_length=200)

    # Index which says which card is now used.
    current_card_index = models.IntegerField(default=0)

    MAX_NUM_OF_CARDS_IN_SESSION = 10

    @classmethod
    def create_or_get_train_session(cls,
                                    userprofile,
                                    deck,
                                    train_pool,
                                    all_cards):
        try:
            train_session = TrainSession.objects.get(userprofile=userprofile,
                                                     deck=deck)
        except TrainSession.DoesNotExist:
            train_session = cls.create_train_session(userprofile,
                                                     deck,
                                                     train_pool,
                                                     all_cards)
        return train_session

    @classmethod
    def create_train_session(cls, userprofile, deck, train_pool, all_cards):
        # Retrieve cards from training pool.
        train_cards_objects = train_pool.train_cards.filter(
            time_to_show__lte=datetime.datetime.now())

        # If there are no cards in train pool then it doesn't make sense to
        # create new session.
        if not len(train_cards_objects):
            return None

        # Specify what cards from training pool will be used in this session.
        train_cards_ids = [str(train_cards_object.id)
                           for train_cards_object in train_cards_objects]
        random.shuffle(train_cards_ids)
        if not all_cards:
            train_cards_ids = (
                train_cards_ids[0:cls.MAX_NUM_OF_CARDS_IN_SESSION])

        train_session = TrainSession(userprofile=userprofile, deck=deck)
        train_session.save()

        # Training cards are represented in session as comma separated list
        # of training cards ids.
        train_session.train_cards = ",".join(train_cards_ids)

        # Set that first training card will be shown.
        train_session.current_card_index = 0
        train_session.save()
        return train_session

    def get_train_card(self):
        # Train cards are kept in session as comma separated ids so here
        # we unpack them.
        train_cards_objects = self.train_cards.split(",")

        # All cards were used so no card will be returned in this case.
        if self.current_card_index >= len(train_cards_objects):
            return None
        id_of_train_card = int(train_cards_objects[self.current_card_index])
        return TrainCard.objects.get(id=id_of_train_card)

    def increase_train_card_index(self):
        """Make that next card will be returned from given session."""
        self.current_card_index += 1
