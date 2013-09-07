=========
Changelog
=========

==========
Unreleased
==========

=====
0.1.0
=====

* Add: Skeleton of Django app
* Add: pep8, pyflakes and test scripts
* Add: Static JS and CSS
* Add: Shelf can be added
* Add: Shelf can be edited and deleted
* Add: Deck can be added, edited and deleted
* Add: Some functional tests based on Robot Framework
* Add: Card can be added, edited and deleted
* Add: Refactored tests - added shortcuts to add shelf, deck, card
* Add: Markdown support
* Add: Number of cards in deck are shown on shelf page
* Add: User can register
* Add: User can login and logout
* Add: Unauthorized users are not able to modify all content of page
* Add: User can see by default page with his taken shelves
* Add: Shelf can be started and stopped by user
* Add: Started shelves are present on user shelf page
* Add: User can start to train a deck (new session is started)
* Add: If user aborts training a deck then he can continue the deck session later
* Add: User cannot use training sessions of other users
* Add: Show answer button added
* Add: SuperMemo2 algorithm implemented for show time calculation for card
* Add: Max 10 cards are chosen for one session
* Add: Backup of database is made for database for some operations
* Add: When user adds some card then he is redirected to page to add another card
* Add: There is also the second option to create session with all cards in deck
* Add: The identical questions in cards can't be placed in single deck
* Add: Text after Markdown transformation is saved in database in order to make cards loading faster
* Add: Replaced pep8 and pyflakes with flake8
* Add: User can export and import database as XML file
* Add: User can upload images when adding or editing card
* Add: User can change order of decks
