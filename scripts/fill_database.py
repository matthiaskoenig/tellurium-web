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

ARCHIVE_DIRS = [
    os.path.join(FILE_DIR, "../archives"),
    # os.path.join(FILE_DIR, "../../sedml-test-suite/archives"),
    # os.path.join(FILE_DIR, "../../sedml-test-suite/archives/biomodels"),
    # os.path.join(FILE_DIR, "../../sedml-test-suite/archives/jws"),
    # os.path.join(FILE_DIR, "../../sedml-test-suite/archives/specification/"),
    # os.path.join(FILE_DIR, "../../sed-ml/specification/level-1-version-3/examples/__omex__"),
]

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
from django.contrib.auth.models import User
from collections import namedtuple

UserDef = namedtuple('UserDef', ['username', 'first_name', 'last_name', 'email', 'superuser'])
user_defs = [
    UserDef("janekg89", "Jan", "Grzegorzewski", "janekg89@hotmail.de", True),
    UserDef("mkoenig", "Matthias", "König", "konigmatt@googlemail.com", True),
    UserDef("testuser", False, False, False, False),
    UserDef("global", False, False, False, False)]


def get_omex_file_paths(ARCHIVE_DIRS):

    # list files
    omex_files = []
    for archive_dir in ARCHIVE_DIRS:
        for subdir, dirs, files in os.walk(archive_dir):
            for file in files:
                path = os.path.join(subdir, file)
                if os.path.isfile(path) and (path.endswith('.omex') or path.endswith('.sedx')):
                    omex_files.append(path)
    return omex_files


def add_archives_to_database():
    """ Add archives to database.

    :return:
    """
    # list files
    omex_files = get_omex_file_paths(ARCHIVE_DIRS)

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
            global_user = User.objects.get(username="global")
            new_archive.user = global_user
            new_archive.file.save(name, django_file, save=False)
            new_archive.md5 = hash_for_file(f, hash_type='MD5')
            new_archive.full_clean()
            new_archive.save()

            # add Tags
            # tag, created = Tag.objects.get_or_create(name="test", type=Tag.TagType.misc)
            # if created:
            #     tag.save()
            # new_archive.tags.add(tag)

            tags_info = comex.tags_info(f)
            print(tags_info)
            for tag_info in tags_info:
                tag, created = Tag.objects.get_or_create(name=tag_info.name,
                                                         category=tag_info.category)
                if created:
                    tag.save()
                new_archive.tags.add(tag)



def create_users(user_defs, delete_all=True):
    """ Create users in database from user definitions.

    :param delete_all: deletes all existing users
    :return:
    """
    if not user_defs:
        user_defs = []

    # deletes all users
    if delete_all:
        User.objects.all().delete()

    # adds user to database
    for user_def in user_defs:
        if user_def.superuser:
            user = User.objects.create_superuser(username=user_def.username, email=user_def.email,
                                                 password= os.environ['DJANGO_ADMIN_PASSWORD'])
        else:
            user = User.objects.create_user(username=user_def.username, email=user_def.email,
                                            password= os.environ['DJANGO_ADMIN_PASSWORD'])
        user.last_name = user_def.last_name
        user.first_name = user_def.first_name
        user.save()

    # display users
    for user in User.objects.all():
        print('\t', user.username, user.email, user.password)

if __name__ == "__main__":

    print('-'*80)
    print('Creating archives')
    print('-' * 80)
    create_users(user_defs=user_defs, delete_all=True)
    add_archives_to_database()
