"""
Setup of archive database.
Database is populated from set of OMEX archives.

necessary to empty database
$ python manage.py flush

The canonical way to accomplish this is fixtures -
the loaddata and dumpdata commands, but these seem to be more
useful when you already have some data in the DB.

http://eli.thegreenplace.net/2014/02/15/programmatically-populating-a-django-database
"""

from __future__ import print_function, division
import os
import sys

FILE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
# project directory
PROJECT_DIR = os.path.join(FILE_DIR, "../teweb/")
# directory of omex archives
ARCHIVE_DIR = os.path.join(FILE_DIR, "../archives")

# This is so my local_settings.py gets loaded.
os.chdir(PROJECT_DIR)
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teweb.settings")
sys.path.append(PROJECT_DIR)

# django setup
import django
django.setup()

from combine.models import Archive
from django.core.files import File


def add_archives_to_database():
    """ Add archives to database.

    :return:
    """
    # list files
    files = []
    for f in os.listdir(ARCHIVE_DIR):
        path = os.path.join(ARCHIVE_DIR, f)
        if os.path.isfile(path) and path.endswith('.omex'):
            files.append(path)

    for f in sorted(files):
        print(f)
        name = os.path.basename(f)
        django_file = File(open(f), 'rb')
        new_archive = Archive(name=name)
        new_archive.file.save(name, django_file, save=False)
        new_archive.full_clean()
        new_archive.save()


if __name__ == "__main__":

    print('-'*80)
    print('Creating archives')
    print('-' * 80)
    add_archives_to_database()
