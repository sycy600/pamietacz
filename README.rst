.. image:: https://secure.travis-ci.org/sycy600/pamietacz.png

An application for making notes in question-answer form which
can be later easy revamped and reviewed.

Features
========

* managing notes in question-answer form
* scheduling algorithm (slightly modified SuperMemo2 algorithm)
  used for reviewing notes
* Markdown support
* sharing notes - import/export as XML file

Basics
======

Get ``buildout``::

    python2.7 bootstrap.py

Create project structure::

    bin/buildout

Initialize database::

    bin/django syncdb

Run application (application is accessible at http://localhost:8000)::

    bin/django runserver --settings=pamietacz.production

Testing
=======

Unit tests are placed in directory ``src/pamietacz/tests``.

Functional tests are placed in directory ``functional_tests``.

The pattern for test filename is ``*_tests.py``.

Run only unit tests::

    bin/unit-tests
    
Run only functional tests::

    bin/functional-tests

Run unit tests, check flake8::

    bin/check
    
Run functional tests, unit tests, flake8::

    bin/long-check

Run single functional tests::

    bin/functional-tests functional_tests/card.txt

Data migration
==============

To migrate the data to other environment, dump database as XML file
and load it in other environment. Also copy images placed in
``uploaded`` directory.
