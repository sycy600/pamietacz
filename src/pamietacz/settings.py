import os

HERE = os.path.dirname(__file__)
SECRET_KEY = "very secret"
ROOT_URLCONF = "pamietacz.urls"
TEMPLATE_DIRS = (os.path.join(HERE, "templates"),)

INSTALLED_APPS = (
    "django.contrib.staticfiles",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.humanize",
    "pamietacz",
)

STATIC_URL = '/static/'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "mydatabase"
    }
}

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login/"

AUTH_USER_MODEL = "pamietacz.UserProfile"
