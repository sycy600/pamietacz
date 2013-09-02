from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Form, FileField, ImageField
from models import Shelf, Deck, Card, UserProfile


class ShelfForm(ModelForm):
    class Meta:
        model = Shelf


class DeckForm(ModelForm):
    class Meta:
        model = Deck
        fields = ('name',)


class CardForm(ModelForm):
    def __init__(self, deck_id=None, *args, **kwargs):
        super(CardForm, self).__init__(*args, **kwargs)
        self.deck_id = deck_id

    def clean(self):
        cleaned_data = super(CardForm, self).clean()
        if "question" not in cleaned_data or "answer" not in cleaned_data:
            return cleaned_data
        cleaned_data["question"] = cleaned_data["question"].strip()
        cleaned_data["answer"] = cleaned_data["answer"].strip()

        # Check if question is not already in this deck.
        if self.deck_id is not None:
            cards = Card.objects.filter(deck_id=self.deck_id)
            current_card_id = None
            if hasattr(self.instance, "id"):
                current_card_id = self.instance.id

            # Check if there is no other card with the same question
            # in database for this deck. However if we edit the same card
            # then it should be okay to add it again to database with the same
            # question because we still have unique question in the same
            # deck.
            for card in cards:
                if card.question == cleaned_data["question"]:
                    # Raise error only if we add new card or when we edit
                    # one card but the same question is in some different
                    # card.
                    if ((current_card_id is not None and
                            current_card_id != card.id)
                            or current_card_id is None):
                        raise ValidationError((u"The question for this"
                                               " card already exists in"
                                               " this deck."))
        return cleaned_data

    class Meta:
        model = Card
        fields = ('question', 'answer')


class DataDumpUploadFileForm(Form):
    data_dump_file = FileField()


class UserProfileCreationForm(UserCreationForm):
    UserCreationForm.Meta.model = UserProfile

    def clean_username(self):
        cleaned_username = self.cleaned_data["username"]
        if UserProfile.objects.filter(username=cleaned_username).exists():
            raise ValidationError(self.error_messages['duplicate_username'])
        return cleaned_username


class UploadedImage(Form):
    uploaded_image = ImageField()
