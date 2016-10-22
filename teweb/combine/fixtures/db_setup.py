"""
Setup of archive database.
Database is populated from set of OMEX archives.

The canonical way to accomplish this is fixtures -
the loaddata and dumpdata commands, but these seem to be more
useful when you already have some data in the DB.

http://eli.thegreenplace.net/2014/02/15/programmatically-populating-a-django-database
"""

from __future__ import print_function, division
import os
import sys

proj_path = "../../../teweb/"

# This is so my local_settings.py gets loaded.
os.chdir(proj_path)
print(os.getcwd())
proj_path = os.getcwd()

# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teweb.settings")
sys.path.append(proj_path)
print(sys.path)


import django
django.setup()
from teweb.combine.models import Archive

# necessary to flush
# python manage.py flush

# directory of omex archives
ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           "../../../archives")

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
            files.append(f)

    for f in sorted(files):
        print(f)
        name = os.path.basename(f)
        new_archive = Archive(name=name, file=File(open(f)))
        new_archive.full_clean()
        new_archive.save()


if __name__ == "__main__":

    """
    archive = Archive.objects.get(pk=10)
    print(archive)
    get_content(archive)
    """

    print('-'*80)
    print('Creating archives')
    print('-' * 80)
    add_archives_to_database()
