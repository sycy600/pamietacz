from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.forms.util import ErrorList
from django.http import Http404
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from forms import (ShelfForm,
                   DeckForm,
                   CardForm,
                   DataDumpUploadFileForm,
                   UserProfileCreationForm,
                   UploadedImage)
from models import Shelf, Deck, Card, TrainSession, TrainPool, TrainCard
import datetime
from collections import OrderedDict
from utils import backup
from dump_load import (dump_data_as_xml,
                       load_data_as_xml,
                       XMLDataDumpException)
from lxml import etree


def shelf_list(request):
    """Show all shelves. On this page shelves can be managed."""
    all_shelves = Shelf.objects.all()
    started_shelves_ids = None
    if request.user.is_authenticated():
        user_profile = request.user
        started_shelves = user_profile.shelves.all()
        started_shelves_ids = [shelf.id for shelf in started_shelves]
    return render(request,
                  "shelf_list.html",
                  {"all_shelves": all_shelves,
                   "started_shelves_ids": started_shelves_ids})


@login_required
@backup
@require_http_methods(["GET", "POST"])
def add_edit_shelf(request, shelf_id=None):
    if shelf_id:
        shelf = get_object_or_404(Shelf, pk=shelf_id)
    else:
        shelf = Shelf()
    if request.method == "GET":
        shelf_form = ShelfForm(instance=shelf)
    elif request.method == "POST":
        shelf_form = ShelfForm(request.POST, instance=shelf)
        if shelf_form.is_valid():
            shelf_form.save()
            return redirect(reverse("pamietacz.views.shelf_list"))
    return render(request,
                  "add_edit_shelf.html",
                  {"shelf_form": shelf_form,
                   "action": request.get_full_path()})


@login_required
@backup
@require_http_methods(["GET"])
def delete_shelf(request, shelf_id):
    shelf = get_object_or_404(Shelf, pk=shelf_id)
    shelf.delete()
    return redirect(reverse("pamietacz.views.shelf_list"))


@require_http_methods(["GET"])
def show_shelf(request, shelf_id):
    """Show what decks are available for specific shelf."""
    shelf = get_object_or_404(Shelf, pk=shelf_id)
    decks = Deck.objects.filter(shelf=shelf).order_by("order")
    return render(request,
                  "show_shelf.html",
                  {"shelf": shelf, "decks": decks})


@login_required
@backup
@require_http_methods(["GET", "POST"])
def add_edit_deck(request, shelf_id=None, deck_id=None):
    if deck_id:
        deck = get_object_or_404(Deck, pk=deck_id)
    else:
        deck = Deck()
    if request.method == "GET":
        deck_form = DeckForm(instance=deck)
    elif request.method == "POST":
        deck_form = DeckForm(request.POST, instance=deck)
        if deck_form.is_valid():
            deck = deck_form.save(commit=False)
            if not hasattr(deck, "shelf"):
                shelf = get_object_or_404(Shelf, pk=shelf_id)
                deck.shelf = shelf
            else:
                shelf_id = deck.shelf.id
            deck.save()
            return redirect(reverse("pamietacz.views.show_shelf",
                                    args=(shelf_id,)))
    return render(request,
                  "add_edit_deck.html",
                  {"deck_form": deck_form,
                   "action": request.get_full_path()})


@login_required
@backup
@require_http_methods(["GET"])
def delete_deck(request, deck_id):
    deck = get_object_or_404(Deck, pk=deck_id)
    shelf_id = deck.shelf.id
    deck.delete()
    return redirect(reverse("pamietacz.views.show_shelf", args=(shelf_id,)))


@login_required
@backup
@require_http_methods(["GET"])
def move_deck(request, deck_id, direction):
    """Move decks up or down so order of decks within one shelf can be
    changed."""
    deck = get_object_or_404(Deck, pk=deck_id)
    shelf_id = deck.shelf.id
    if direction in ("up", "down"):
        deck.move(direction)
    else:
        raise Http404
    return redirect(reverse("pamietacz.views.show_shelf", args=(shelf_id,)))


@require_http_methods(["GET"])
def show_deck(request, deck_id):
    """Show what cards are available for specific deck."""
    deck = get_object_or_404(Deck, pk=deck_id)
    cards = Card.objects.filter(deck=deck).order_by("id")
    return render(request,
                  "show_deck.html",
                  {"deck": deck, "cards": cards})


@login_required
@backup
@require_http_methods(["GET", "POST"])
def add_edit_card(request, deck_id=None, card_id=None):
    if card_id:
        card = get_object_or_404(Card, pk=card_id)
    else:
        card = Card()
    if request.method == "GET":
        card_form = CardForm(instance=card)
    elif request.method == "POST":
        if deck_id is None:
            deck_id = card.deck.id
        card_form = CardForm(data=request.POST,
                             instance=card,
                             deck_id=deck_id)
        if card_form.is_valid():
            card = card_form.save(commit=False)
            if not hasattr(card, "deck"):
                # Card is added.
                deck = get_object_or_404(Deck, pk=deck_id)
                card.deck = deck
                card.save()

                # If new card is added then we need also to add it
                # to train pools so user can train it also from now.
                trainpools = TrainPool.objects.filter(deck=deck)
                for train_pool in trainpools:
                    train_card = TrainCard(card=card)
                    train_card.save()
                    train_pool.train_cards.add(train_card)
                    train_pool.save()
                return redirect(request.path)
            else:
                # Card is edited.
                card.save()
                return redirect(reverse("pamietacz.views.show_deck",
                                        args=(deck_id,)))
    return render(request,
                  "add_edit_card.html",
                  {"card_form": card_form,
                   "action": request.get_full_path()})


@login_required
@require_http_methods(["POST"])
def upload_image(request):
    """Upload image endpoint for AJAX requests."""
    uploaded_image = UploadedImage(request.POST, request.FILES)
    if uploaded_image.is_valid():
        filename = request.FILES["uploaded_image"].name
        content_of_file = ContentFile(request.FILES["uploaded_image"].read())
        saved_as = default_storage.save(filename, content_of_file)
        return HttpResponse(saved_as)
    return HttpResponseBadRequest()


@login_required
@backup
@require_http_methods(["GET"])
def delete_card(request, card_id):
    card = get_object_or_404(Card, pk=card_id)
    deck_id = card.deck.id
    card.delete()
    return redirect(reverse("pamietacz.views.show_deck", args=(deck_id,)))


@backup
@require_http_methods(["GET", "POST"])
def register_new_user(request):
    if request.method == "GET":
        register_form = UserCreationForm()
    elif request.method == "POST":
        register_form = UserProfileCreationForm(request.POST)
        if register_form.is_valid():
            register_form.save()
            return redirect(reverse("pamietacz.views.user_shelves"))
    return render(request,
                  "register.html", {"register_form": register_form,
                                    "action": request.get_full_path()})


@login_required
@require_http_methods(["GET"])
def user_shelves(request):
    """Show what shelves user started to learn."""
    profile = request.user
    shelves = profile.shelves.all()
    items_to_train_dict = {}
    for shelf in shelves:
        train_pools = TrainPool.objects.filter(
            userprofile=profile,
            deck__in=shelf.deck_set.all())
        items_to_train_dict[shelf.id] = 0
        for train_pool in train_pools:
            items_to_train_dict[shelf.id] +=\
                train_pool.number_of_cards_to_repeat_now()
    return render(request,
                  "user_shelves.html",
                  {"all_shelves": shelves,
                   "items_to_train_dict": items_to_train_dict})


@login_required
@backup
@require_http_methods(["GET"])
def start_shelf(request, shelf_id):
    """Start to learn new shelf."""
    shelf = get_object_or_404(Shelf, pk=shelf_id)
    profile = request.user
    if profile.shelves.filter(pk=shelf_id).exists():
        # User has already started to learn this shelf.
        redirect(reverse("pamietacz.views.shelf_list"))
    profile.shelves.add(shelf)
    profile.save()
    return redirect(reverse("pamietacz.views.shelf_list"))


@login_required
@backup
@require_http_methods(["GET"])
def stop_shelf(request, shelf_id):
    """Stop to learn shelf so that all training history will be
    gone."""
    shelf = get_object_or_404(Shelf, pk=shelf_id)
    profile = request.user
    profile.shelves.remove(shelf)
    profile.save()
    decks = Deck.objects.filter(shelf=shelf)
    for deck in decks:
        trainpools = TrainPool.objects.filter(deck=deck,
                                              userprofile=profile)
        for trainpool in trainpools:
            trainpool.train_cards.all().delete()
            trainpool.delete()
        TrainSession.objects.filter(deck=deck,
                                    userprofile=profile).delete()
    return redirect(request.GET.get("next", "/"))


@login_required
@require_http_methods(["GET"])
def user_show_shelf(request, shelf_id):
    """Show what decks within started shelf are available to train
    for specific user."""
    shelf = get_object_or_404(Shelf, pk=shelf_id)
    profile = request.user
    if not profile.started_shelf(shelf):
        raise Http404
    decks = Deck.objects.filter(shelf=shelf).order_by("order")

    # Check if some sessions were started and if so
    # then display link Continue session instead of Train.
    started_sessions = TrainSession.objects.filter(deck__in=decks,
                                                   userprofile=profile)
    decks_ids = [train_session.deck.id
                 for train_session in started_sessions]

    # Retrieve train pools (card sets) for specific user.
    train_pools = TrainPool.objects.filter(userprofile=profile,
                                           deck__in=decks)

    # Get the number of cards ready to repeat for specific training pool.
    number_of_cards_to_repeat_now = {}
    for train_pool in train_pools:
        number_of_cards_to_repeat_now[train_pool.deck.id] =\
            train_pool.number_of_cards_to_repeat_now()

    return render(request,
                  "user_show_shelf.html",
                  {"shelf": shelf,
                   "decks": decks,
                   "started_train_sessions_decks_id": decks_ids,
                   "number_of_cards_to_repeat_now":
                   number_of_cards_to_repeat_now})


@login_required
@backup
@require_http_methods(["GET"])
def user_train_deck(request, deck_id, all_cards=False):
    """Prepare deck to be trained -
    create/get train pool, create/get train session."""
    deck = get_object_or_404(Deck, pk=deck_id)
    shelf = deck.shelf
    profile = request.user
    if not profile.started_shelf(shelf):
        raise Http404
    train_pool = TrainPool.create_or_get_train_pool(profile, deck)
    train_session = TrainSession.create_or_get_train_session(profile,
                                                             deck,
                                                             train_pool,
                                                             all_cards)

    # New session was started.
    if train_session is None:
        return redirect(reverse("pamietacz.views.user_show_shelf",
                                args=(shelf.id,)))

    # Current session will be continued.
    return redirect(reverse("pamietacz.views.user_train_session",
                            args=(train_session.id,)))


ANSWER_PARAMETER_NAME = "Answer"
AVAILABLE_ANSWERS = OrderedDict([("Good", 5), ("Bad", 0)])


@login_required
@require_http_methods(["GET", "POST"])
def user_train_session(request, session_id):
    """This method displays appropriate question for given session."""
    train_session = get_object_or_404(TrainSession, pk=session_id)
    profile = request.user
    # Check if user can do this session.
    if train_session.userprofile.id != profile.id:
        raise PermissionDenied

    # Check if answer was sent - if yes then get new question.
    answer = request.POST.get(ANSWER_PARAMETER_NAME, None)
    if answer in AVAILABLE_ANSWERS:

        # Get a card for which answer is given.
        train_card = train_session.get_train_card()

        # Calculate new time interval for given answer.
        if train_card is not None:
            train_card.calculate_interval(AVAILABLE_ANSWERS[answer])
            train_card.save()
        train_session.increase_train_card_index()

    # Get new card.
    train_card = train_session.get_train_card()

    # If there are no cards left, then finish session.
    if train_card is None:
        shelf_id = train_session.deck.shelf.id
        train_session.delete()
        return redirect(reverse("pamietacz.views.user_show_shelf",
                                args=(shelf_id,)))

    train_session.save()

    return render(request,
                  "user_train_session.html",
                  {"train_card": train_card,
                   "request": request,
                   "answer_parameter_name": ANSWER_PARAMETER_NAME,
                   "available_answers": AVAILABLE_ANSWERS})


@login_required
@require_http_methods(["GET"])
def user_show_deck(request, deck_id):
    """Show cards for given deck with the next time to reply for specific
    user."""
    deck = get_object_or_404(Deck, pk=deck_id)
    profile = request.user
    if not profile.started_shelf(deck.shelf):
        raise Http404

    # Show 404 if this training for this deck was not started.
    try:
        train_pool = TrainPool.objects.get(deck=deck, userprofile=profile)
        train_cards = train_pool.train_cards.all().order_by('time_to_show')
    except TrainPool.DoesNotExist:
        raise Http404
    return render(request,
                  "user_show_deck.html",
                  {"deck": deck,
                   "train_cards": train_cards,
                   "datetime_now": datetime.datetime.now()})


@require_http_methods(["GET"])
def dump_data(request):
    """Save all shelf/deck/card data and return as XML file. User specific
    is not dumped."""
    file_content = dump_data_as_xml()
    file_response = HttpResponse(file_content, content_type="application/xml")
    content_disposition = 'attachment; filename="dump_data.xml"'
    file_response["Content-Disposition"] = content_disposition
    return file_response


@login_required
@backup
@require_http_methods(["GET", "POST"])
def load_data(request):
    """Load data (shelf/deck/card) from XML file to database."""
    if request.method == "GET":
        upload_form = DataDumpUploadFileForm()
    elif request.method == "POST":
        upload_form = DataDumpUploadFileForm(request.POST, request.FILES)
        if upload_form.is_valid():
            try:
                load_data_as_xml(request.FILES["data_dump_file"])
                return redirect(reverse("pamietacz.views.shelf_list"))
            except (XMLDataDumpException, etree.XMLSyntaxError) as e:
                upload_form._errors["data_dump_file"] = ErrorList()
                error_message = "Error while parsing XML: %s" % str(e)
                upload_form._errors["data_dump_file"].append(error_message)
    return render(request, "load_data.html",
                  {"data_dump_upload_file_form": upload_form,
                   "action": request.get_full_path()})
