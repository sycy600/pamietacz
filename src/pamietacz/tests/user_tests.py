from django.http import (HttpResponseRedirect,
                         HttpResponseForbidden,
                         HttpResponseNotFound)
from pamietacz.models import (Shelf,
                              Deck,
                              Card,
                              TrainSession,
                              TrainPool,
                              TrainCard,
                              UserProfile)
from test_utils import (add_shelf,
                        add_deck,
                        add_card,
                        TestCaseWithAuthentication)
import datetime


class StartStopShelfTests(TestCaseWithAuthentication):
    def test_start_shelf(self):
        shelf_name = "Some nice shelf"

        # Shelf is not shown on user shelf list and on all shelves list.
        r = self.client.get("/")
        self.assertNotIn(shelf_name, r.content)
        r = self.client.get("/shelf/list/")
        self.assertNotIn(shelf_name, r.content)

        add_shelf(self.client, shelf_name)

        # Shelf is now shown on all shelves list but
        # user still didn't take this shelf.
        r = self.client.get("/")
        self.assertNotIn(shelf_name, r.content)
        r = self.client.get("/shelf/list/")
        self.assertIn(shelf_name, r.content)

        # Start shelf.
        shelf = Shelf.objects.all()[0]
        r = self.client.get("/user/shelf/%s/start/" % shelf.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # Now this shelf is shown on user list and on all shelves list.
        r = self.client.get("/")
        self.assertIn(shelf_name, r.content)
        r = self.client.get("/shelf/list/")
        self.assertIn(shelf_name, r.content)

    def test_start_shelf_twice(self):
        shelf_name = "Some nice shelf"

        add_shelf(self.client, shelf_name)

        # No shelves are now started by user.
        shelves = UserProfile.objects.all()[0].shelves.all()
        self.assertEqual(len(shelves), 0)

        # Start a shelf.
        shelf = Shelf.objects.all()[0]
        r = self.client.get("/user/shelf/%s/start/" % shelf.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # One shelf is started by user.
        shelves = UserProfile.objects.all()[0].shelves.all()
        self.assertEqual(len(shelves), 1)

        # Start the same shelf again.
        r = self.client.get("/user/shelf/%s/start/" % shelf.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # Still only one shelf is connected with user.
        shelves = UserProfile.objects.all()[0].shelves.all()
        self.assertEqual(len(shelves), 1)

    def test_start_and_stop_shelf(self):
        shelf_name = "Some nice shelf"

        add_shelf(self.client, shelf_name)

        # Start shelf.
        shelf = Shelf.objects.all()[0]
        r = self.client.get("/user/shelf/%s/start/" % shelf.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # One shelf is started.
        shelves = UserProfile.objects.all()[0].shelves.all()
        self.assertEqual(len(shelves), 1)

        # Stop shelf.
        r = self.client.get("/user/shelf/%s/stop/" % shelf.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # Zero shelves are started.
        shelves = UserProfile.objects.all()[0].shelves.all()
        self.assertEqual(len(shelves), 0)

    def test_stop_shelf_before_starting(self):
        shelf_name = "Some nice shelf"

        add_shelf(self.client, shelf_name)

        # No shelves are started.
        shelves = UserProfile.objects.all()[0].shelves.all()
        self.assertEqual(len(shelves), 0)

        # Try to stop shelf even if not shelves are started.
        shelf = Shelf.objects.all()[0]
        r = self.client.get("/user/shelf/%s/stop/" % shelf.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # Still no shelves are started.
        shelves = UserProfile.objects.all()[0].shelves.all()
        self.assertEqual(len(shelves), 0)

    def test_start_or_stop_link_is_present(self):
        """If shelf is not started then there is present on all shelf list
        the start button, otherwise stop button."""

        shelf_name = "Some nice shelf"

        add_shelf(self.client, shelf_name)

        # When shelf is not started then there is Start link.
        r = self.client.get("/shelf/list/")
        self.assertIn("Start", r.content)
        self.assertNotIn("Stop", r.content)

        # Start shelf.
        shelf = Shelf.objects.all()[0]
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # When shelf is started then only Stop link is present.
        r = self.client.get("/shelf/list/")
        self.assertIn("Stop", r.content)
        self.assertNotIn("Start", r.content)

        # Stop shelf.
        self.client.get("/user/shelf/%s/stop/" % shelf.id)

        # Shelf was stopped so now it can be started again.
        r = self.client.get("/shelf/list/")
        self.assertIn("Start", r.content)
        self.assertNotIn("Stop", r.content)


class TrainTests(TestCaseWithAuthentication):
    def test_start_training(self):
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

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # Train a new deck.
        r = self.client.get("/user/deck/%s/train/" % deck.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # One training session is present.
        trainsessions = TrainSession.objects.all()
        session = trainsessions[0]
        self.assertEqual(len(trainsessions), 1)

        # One training pool was created.
        trainpools = TrainPool.objects.all()
        self.assertEqual(len(trainpools), 1)

        # One train card was created from existing cards.
        traincards = TrainCard.objects.all()
        self.assertEqual(len(traincards), 1)

        # Check first question.
        r = self.client.get("/user/train/session/%s/" % session.id)
        self.assertIn(card_question, r.content)

        # There are no more questions, so training session is finished
        # and user is redirected to shelf page.
        r = self.client.post("/user/train/session/%s/" % session.id,
                             {"Answer": "Good"})
        self.assertIn("user/shelf/%s/show/" % shelf.id, r.get("location"))

        # There are no training sessions now.
        trainsessions = TrainSession.objects.all()
        self.assertEqual(len(trainsessions), 0)

        # But training pool is still present.
        trainpools = TrainPool.objects.all()
        self.assertEqual(len(trainpools), 1)

        # The training cards was also not deleted.
        traincards = TrainCard.objects.all()
        self.assertEqual(len(traincards), 1)

        # Stop shelf.
        self.client.get("/user/shelf/%s/stop/" % shelf.id)

        # But training pool is still present.
        trainpools = TrainPool.objects.all()
        self.assertEqual(len(trainpools), 0)

        # The training cards was also not deleted.
        traincards = TrainCard.objects.all()
        self.assertEqual(len(traincards), 0)

    def test_start_training_when_there_are_no_cards(self):
        """Session is not created when there are no cards to train."""
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)

        deck = Deck.objects.all()[0]

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # Train a deck with no cards there.
        r = self.client.get("/user/deck/%s/train/" % deck.id, follow=True)
        self.assertEqual(r.status_code, 200)

        # Train pool was created.
        trainpools = TrainPool.objects.all()
        self.assertEqual(len(trainpools), 1)

        # But train session not because there are no cards in train pool.
        trainsessions = TrainSession.objects.all()
        self.assertEqual(len(trainsessions), 0)

    def test_start_training_session_index_only_increases_after_answer(self):
        """Only when answer is given then index of session with new card
        increases."""

        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        card_question1 = "What is it?"
        card_answer1 = "This is that."
        card_question2 = "What was it?"
        card_answer2 = "This was that."

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)

        # Add two cards.
        deck = Deck.objects.all()[0]
        add_card(self.client, deck.id, card_question1, card_answer1)
        add_card(self.client, deck.id, card_question2, card_answer2)

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # Train a new deck.
        self.client.get("/user/deck/%s/train/" % deck.id)

        # One session was started.
        trainsessions = TrainSession.objects.all()
        session = trainsessions[0]
        self.assertEqual(len(trainsessions), 1)

        # Figure out which card was now chosen.
        r = self.client.get("/user/train/session/%s/" % session.id)
        if card_question1 in r.content:
            current_question = card_question1
            next_question = card_question2
        else:
            current_question = card_question2
            next_question = card_question1
        self.assertIn(current_question, r.content)

        # Check if the same question was shown if no answer was given.
        r = self.client.get("/user/train/session/%s/" % session.id)
        self.assertIn(current_question, r.content)

        # Answer was given so next question is now shown.
        r = self.client.post("/user/train/session/%s/" % session.id,
                             {"Answer": "Bad"})
        self.assertIn(next_question, r.content)

        # Answer is given and training session is finished.
        self.client.post("/user/train/session/%s/" % session.id,
                         {"Answer": "Good"})

        # No train sessions are present.
        trainsessions = TrainSession.objects.all()
        self.assertEqual(len(trainsessions), 0)

    def test_add_delete_new_cards_and_it_is_also_updated_in_train_pool(self):
        """If new cards are added to deck then it should be also
        updated in train pool. If some card is deleted then train card
        should be deleted too."""

        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        card_question1 = "What is it?"
        card_answer1 = "This is that."
        card_question2 = "What was it?"
        card_answer2 = "This was that."

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)

        # Add two cards.
        deck = Deck.objects.all()[0]

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # No train pools are present before starting training.
        trainpools = TrainPool.objects.all()
        self.assertEqual(len(trainpools), 0)

        # No train cards are present if there are no train pools.
        traincards = TrainCard.objects.all()
        self.assertEqual(len(traincards), 0)

        # Train a new deck.
        self.client.get("/user/deck/%s/train/" % deck.id)

        # Training was started so train pool was created.
        trainpools = TrainPool.objects.all()
        self.assertEqual(len(trainpools), 1)

        # But there are no cards so no train cards will be created.
        traincards = TrainCard.objects.all()
        self.assertEqual(len(traincards), 0)

        # Add new card.
        add_card(self.client, deck.id, card_question1, card_answer1)

        # There is still one train pool.
        trainpools = TrainPool.objects.all()
        self.assertEqual(len(trainpools), 1)

        # But when new card was added then new train card for this pool
        # was also created.
        traincards = TrainCard.objects.all()
        self.assertEqual(len(traincards), 1)

        # Add another card.
        add_card(self.client, deck.id, card_question2, card_answer2)

        # There is still one train pool.
        trainpools = TrainPool.objects.all()
        self.assertEqual(len(trainpools), 1)

        # But the second card triggered also creation of new train card.
        traincards = TrainCard.objects.all()
        self.assertEqual(len(traincards), 2)

        # Delete one card.
        cards = Card.objects.all()
        card = cards[0]
        self.client.get("/card/%s/delete/" % card.id)

        # There is still one train pool.
        trainpools = TrainPool.objects.all()
        self.assertEqual(len(trainpools), 1)

        # The train card was also deleted when card was deleted.
        traincards = TrainCard.objects.all()
        self.assertEqual(len(traincards), 1)

    def test_user_cannot_perform_sessions_of_other_users(self):
        """If two users train the same deck, they can't have access
        to the sessions of each other."""

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

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # Train a new deck.
        r = self.client.get("/user/deck/%s/train/" % deck.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # Train session and get correct result because this user started it.
        trainsessions = TrainSession.objects.all()
        session = trainsessions[0]
        r = self.client.get("/user/train/session/%s/" % session.id)
        self.assertEqual(r.status_code, 200)

        # Login as other user.
        UserProfile.objects.create_user(username="Other", password="Password")
        self.client.logout()
        self.client.login(username="Other", password="Password")

        # Try to train session of other user - it's forbidden.
        r = self.client.get("/user/train/session/%s/" % session.id)
        self.assertEqual(r.status_code, HttpResponseForbidden.status_code)

    def test_train_or_continue_session(self):
        """If user started session then he will see continue session instead
        of train on shelf page."""

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

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # User didn't start session so there is shown Train link.
        r = self.client.get("/user/shelf/%s/show/" % shelf.id)
        self.assertIn("Train", r.content)
        self.assertNotIn("Continue session", r.content)

        # Train a new deck.
        self.client.get("/user/deck/%s/train/" % deck.id)

        # User started session so there is shown only Continue session link.
        r = self.client.get("/user/shelf/%s/show/" % shelf.id)
        self.assertNotIn("Train", r.content)
        self.assertIn("Continue session", r.content)

    def test_show_shelf_page_when_user_didnt_start_shelf(self):
        """If user didn't start shelf then he shouldn't see shelf page."""

        shelf_name = "Some nice shelf"

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]

        # User didn't start shelf so he cannot see shelf page.
        r = self.client.get("/user/shelf/%s/show/" % shelf.id)
        self.assertEqual(r.status_code, HttpResponseNotFound.status_code)

    def test_start_training_and_check_answer_time_on_good_answer(self):
        """When the answer is good then the new time to show card is
        calculated and card will be shown later."""
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

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # Train a new deck.
        r = self.client.get("/user/deck/%s/train/" % deck.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # Get current session and time to show for card.
        trainsessions = TrainSession.objects.all()
        session = trainsessions[0]
        traincards = TrainCard.objects.all()
        traincard = traincards[0]
        time_to_show = traincard.time_to_show

        # Check first question.
        r = self.client.get("/user/train/session/%s/" % session.id)
        self.assertIn(card_question, r.content)

        # Answer good on first question.
        self.client.post("/user/train/session/%s/" % session.id,
                         {"Answer": "Good"})

        # Get newer calculated time to show for card.
        traincards = TrainCard.objects.all()
        traincard = traincards[0]
        new_time_to_show = traincard.time_to_show

        # Check that new time to show is greater than old time to show.
        self.assertTrue(new_time_to_show > time_to_show)

    def test_start_training_and_check_answer_time_on_wrong_answer(self):
        """When the answer for question is wrong then new time to show for
        card is not calculated."""
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

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # Train a new deck.
        r = self.client.get("/user/deck/%s/train/" % deck.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # Get current session and time to show for card.
        trainsessions = TrainSession.objects.all()
        session = trainsessions[0]
        traincards = TrainCard.objects.all()
        traincard = traincards[0]
        time_to_show = traincard.time_to_show

        # Check first question.
        r = self.client.get("/user/train/session/%s/" % session.id)
        self.assertIn(card_question, r.content)

        # Answer good on first question.
        self.client.post("/user/train/session/%s/" % session.id,
                         {"Answer": "Bad"})

        # Get newer calculated time to show for card.
        traincards = TrainCard.objects.all()
        traincard = traincards[0]
        new_time_to_show = traincard.time_to_show

        # Check that new time to show is greater than old time to show.
        self.assertTrue(new_time_to_show == time_to_show)

    def test_try_to_see_deck_page_before_starting_training(self):
        """If the user started shelf with deck but he didn't
        start to train the deck then he shouldn't see the deck page."""
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

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # Then user tries to see deck page for shelf -
        # but he didn't start training so 404 is returned.
        r = self.client.get("/user/deck/%s/show/" % deck.id)
        self.assertEqual(r.status_code, HttpResponseNotFound.status_code)

        # Then user starts the training and training pool
        # is created this time.
        r = self.client.get("/user/deck/%s/train/" % deck.id)
        self.assertEqual(r.status_code, HttpResponseRedirect.status_code)

        # And user after starting training and creation of
        # training pool can view deck page.
        r = self.client.get("/user/deck/%s/show/" % deck.id)
        self.assertEqual(r.status_code, 200)

    def test_check_the_train_nothing_to_train_link(self):
        """If the time to show for each card is still pending then nothing
        to train should be shown near deck name on shelf page.
        If deck wasn't ever started and training pool was not created for
        deck then train link is present.
        If there is at least one card to train then train link should be
        shown there. If session is started
        but not finished then continue session link should be shown there."""
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        card_question = "What is it?"
        card_answer = "This is that."

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)

        deck = Deck.objects.all()[0]

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # There are yet no cards in deck.
        r = self.client.get("/user/shelf/%s/show/" % shelf.id)
        self.assertIn("Train", r.content)
        self.assertIn("(0)", r.content)

        # Train the deck. There are no cards to train
        # so session is not created.
        self.client.get("/user/deck/%s/train/" % deck.id)

        # Look on shelf page - training pool was created but there are no
        # training cards so there is nothing to train.
        r = self.client.get("/user/shelf/%s/show/" % shelf.id)
        self.assertIn("Nothing to train", r.content)
        self.assertIn("(0 / 0)", r.content)

        # On deck page there are still no train cards to learn.
        r = self.client.get("/user/deck/%s/show/" % deck.id)
        self.assertNotIn("now", r.content)

        # Add some card.
        add_card(self.client, deck.id, card_question, card_answer)

        # Now there is one card to learn which can be learnt "now".
        r = self.client.get("/user/deck/%s/show/" % deck.id)
        self.assertIn("now", r.content)
        self.assertNotIn("from now", r.content)

        # On shelf page there is also shown that one from one card can be
        # learned.
        r = self.client.get("/user/shelf/%s/show/" % shelf.id)
        self.assertIn("Train", r.content)
        self.assertIn("(1 / 1)", r.content)

        # Answer wrong on this card.
        self.client.get("/user/deck/%s/train/" % deck.id)
        trainsessions = TrainSession.objects.all()
        session = trainsessions[0]
        self.client.post("/user/train/session/%s/" % session.id,
                         {"Answer": "Bad"})

        # This card can be still learned because the answer was wrong.
        r = self.client.get("/user/deck/%s/show/" % deck.id)
        self.assertIn("now", r.content)
        self.assertNotIn("from now", r.content)

        # Also the same is shown on shelf page.
        r = self.client.get("/user/shelf/%s/show/" % shelf.id)
        self.assertIn("Train", r.content)
        self.assertIn("(1 / 1)", r.content)

        # Now answer right on this question.
        self.client.get("/user/deck/%s/train/" % deck.id)
        trainsessions = TrainSession.objects.all()
        session = trainsessions[0]
        self.client.post("/user/train/session/%s/" % session.id,
                         {"Answer": "Good"})

        # New time to show was calculated for this card.
        r = self.client.get("/user/deck/%s/show/" % deck.id)
        self.assertIn("23 minutes from now", r.content)

        # And there are currently no cards to learn.
        r = self.client.get("/user/shelf/%s/show/" % shelf.id)
        self.assertIn("Nothing to train", r.content)
        self.assertIn("(0 / 1)", r.content)

    def test_calculate_interval_time(self):
        """Time calculations for right and wrong answer."""
        shelf_name = "Some nice shelf"
        deck_name = "Some nice deck"
        card_question = "What is it?"
        card_answer = "This is that."

        add_shelf(self.client, shelf_name)

        # Add deck.
        shelf = Shelf.objects.all()[0]
        add_deck(self.client, shelf.id, deck_name)

        deck = Deck.objects.all()[0]

        # Add some card.
        add_card(self.client, deck.id, card_question, card_answer)

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # Start deck training.
        self.client.get("/user/deck/%s/train/" % deck.id)

        traincards = TrainCard.objects.all()
        traincard = traincards[0]

        now = datetime.datetime.now()

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 24)

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 144)

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 403)

        # Answer wrong - time is not calculated.
        traincard.calculate_interval(0)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 403)

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 24)

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 144)

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 446)

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 1428)

        # Answer wrong - time is not calculated.
        traincard.calculate_interval(0)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 1428)

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 24)

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 144)

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = (new_time_to_show - now).seconds
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 504)

        # Answer correct.
        traincard.calculate_interval(5)
        new_time_to_show = traincard.time_to_show
        time_deleta_in_seconds = ((new_time_to_show - now).seconds +
                                  (new_time_to_show - now).days * 24 * 60 * 60)
        time_deleta_in_minutes = time_deleta_in_seconds / 60
        self.assertEqual(time_deleta_in_minutes, 1814)

    def test_max_number_of_cards_for_session(self):
        """For one session maximum 10 cards are chosen."""

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

        # Add 20 cards.
        for i in range(20):
            add_card(self.client,
                     deck.id,
                     card_question + str(i),
                     card_answer)

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # Start deck training.
        self.client.get("/user/deck/%s/train/" % deck.id)

        # Maximum 10 cards are in this session.
        trainsessions = TrainSession.objects.all()
        session = trainsessions[0]
        traincards_of_session = session.train_cards.split(",")
        self.assertEqual(len(traincards_of_session), 10)

    def test_train_all_option_gets_all_cards_in_session(self):
        """Except normal train session which gets in session max
        10 cards, there is also an option to train all cards which
        will create session with all cards in given deck.."""

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

        # Add 20 cards.
        for i in range(20):
            add_card(self.client,
                     deck.id,
                     card_question + str(i),
                     card_answer)

        # Start shelf.
        self.client.get("/user/shelf/%s/start/" % shelf.id)

        # Start deck training.
        self.client.get("/user/deck/%s/train/all/" % deck.id)

        # All 20 cards will be put in session.
        trainsessions = TrainSession.objects.all()
        session = trainsessions[0]
        traincards_of_session = session.train_cards.split(",")
        self.assertEqual(len(traincards_of_session), 20)
