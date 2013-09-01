from settings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES["default"]["NAME"] = "functional_test"

MEDIA_ROOT = "functional_tests_uploaded/"
