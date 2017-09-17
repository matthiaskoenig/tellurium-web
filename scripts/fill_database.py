"""
Initial setup of combine archive database.

necessary to empty database
$ python manage.py flush
Use the
$ reinit_db.sh
script which performs the complete reset of the database.

The canonical way to accomplish this is fixtures -
the loaddata and dumpdata commands, but these seem to be more
useful when you already have some data in the DB.

http://eli.thegreenplace.net/2014/02/15/programmatically-populating-a-django-database
"""
import os
import sys
import warnings

FILE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
# project directory
PROJECT_DIR = os.path.join(FILE_DIR, "../teweb/")
# directory of omex archives
# ARCHIVE_DIR = os.path.join(FILE_DIR, "../archives/L1V3")
ARCHIVE_DIR = os.path.join(FILE_DIR, "../archives")

# This is so my local_settings.py gets loaded.
os.chdir(PROJECT_DIR)
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teweb.settings")
sys.path.append(PROJECT_DIR)

# django setup
import django
django.setup()

from combine.models import Archive, Tag, hash_for_file
from combine import comex
from django.core.files import File


def add_archives_to_database():
    """ Add archives to database.

    :return:
    """
    # list files
    omex_files = []

    for subdir, dirs, files in os.walk(ARCHIVE_DIR):
        for file in files:
            path = os.path.join(subdir, file)
            if os.path.isfile(path) and (path.endswith('.omex') or path.endswith('.sedx')):
                omex_files.append(path)

    for f in sorted(omex_files):
        print('-' * 80)
        print(f)
        md5 = hash_for_file(f, hash_type='MD5')
        existing_archive = Archive.objects.filter(md5=md5)
        # archive exists already based on the MD5 checksum
        if len(existing_archive) > 0:
            print("Archive already exists, not recreated: {}".format(f))
        else:
            name = os.path.basename(f)
            django_file = File(open(f, 'rb'))
            new_archive = Archive(name=name)
            new_archive.file.save(name, django_file, save=False)
            new_archive.md5 = hash_for_file(f, hash_type='MD5')
            new_archive.full_clean()
            new_archive.save()

            # add Tags
            tag, created = Tag.objects.get_or_create(name="test", type=Tag.TagType.misc)
            if created:
                tag.save()

            tags_info = comex.tags_info(f)
            for tag_info in tags_info:
                tag, created = Tag.objects.get_or_create(name=tag_info['name'],
                                                         type=tag_info['type'])
                if created:
                    tag.save()

            new_archive.tags.add(tag)

if __name__ == "__main__":

    print('-'*80)
    print('Creating archives')
    print('-' * 80)
    add_archives_to_database()
