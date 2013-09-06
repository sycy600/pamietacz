from django.conf import settings
from datetime import datetime
import os
import shutil


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
