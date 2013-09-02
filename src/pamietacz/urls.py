from django.conf.urls import patterns
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns(
    '',
    (r"^$", "pamietacz.views.user_shelves"),
    (r"^shelf/list/$", "pamietacz.views.shelf_list"),
    (r"^shelf/add/$", "pamietacz.views.add_edit_shelf"),
    (r"^shelf/(?P<shelf_id>\d+)/edit/$", "pamietacz.views.add_edit_shelf"),
    (r"^shelf/(?P<shelf_id>\d+)/delete/$", "pamietacz.views.delete_shelf"),
    (r"^shelf/(?P<shelf_id>\d+)/show/$", "pamietacz.views.show_shelf"),
    (r"^shelf/(?P<shelf_id>\d+)/deck/add/$",
     "pamietacz.views.add_edit_deck"),
    (r"^deck/(?P<deck_id>\d+)/edit/$", "pamietacz.views.add_edit_deck"),
    (r"^deck/(?P<deck_id>\d+)/delete/$", "pamietacz.views.delete_deck"),
    (r"^deck/(?P<deck_id>\d+)/show/$", "pamietacz.views.show_deck"),
    (r"^deck/(?P<deck_id>\d+)/card/add/$",
     "pamietacz.views.add_edit_card"),
    (r"^deck/(?P<deck_id>\d+)/move/(?P<direction>down|up)/$",
     "pamietacz.views.move_deck"),
    (r"^image/upload/$",
     "pamietacz.views.upload_image"),
    (r"^card/(?P<card_id>\d+)/edit/$", "pamietacz.views.add_edit_card"),
    (r"^card/(?P<card_id>\d+)/delete/$", "pamietacz.views.delete_card"),
    (r"^register/$", "pamietacz.views.register"),
    (r"^login/$", "django.contrib.auth.views.login",
     {"template_name": "login.html",
      "authentication_form": AuthenticationForm,
      "extra_context": {"action": "/login/"}}),
    (r"^logout/$", "django.contrib.auth.views.logout", {'next_page': '/'}),
    (r"^user/shelf/(?P<shelf_id>\d+)/start/$",
     "pamietacz.views.start_shelf"),
    (r"^user/shelf/(?P<shelf_id>\d+)/stop/$",
     "pamietacz.views.stop_shelf"),
    (r"^user/shelf/(?P<shelf_id>\d+)/show/$",
     "pamietacz.views.user_show_shelf"),
    (r"^user/deck/(?P<deck_id>\d+)/train/$",
     "pamietacz.views.user_train_deck"),
    (r"^user/deck/(?P<deck_id>\d+)/train/all/$",
     "pamietacz.views.user_train_deck", {"all_cards": True}),
    (r"^user/train/session/(?P<session_id>\d+)/$",
     "pamietacz.views.user_train_session"),
    (r"^user/deck/(?P<deck_id>\d+)/show/$",
     "pamietacz.views.user_show_deck"),
    (r"^data/dump/$", "pamietacz.views.dump_data"),
    (r"^data/load/$", "pamietacz.views.load_data")
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
