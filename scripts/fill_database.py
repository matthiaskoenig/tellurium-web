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

FILE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
PROJECT_DIR = os.path.join(FILE_DIR, "../teweb/")

# directories with OMEX archives
ARCHIVE_DIRS = [
    os.path.join(FILE_DIR, "../archives"),
    # os.path.join(FILE_DIR, "../archives/annotation"),
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

from combine.data import UserDef, create_users, add_archives_to_database

# user definitions for database
user_definitions = [
    UserDef("janekg89", "Jan", "Grzegorzewski", "janekg89@hotmail.de", True),
    UserDef("mkoenig", "Matthias", "König", "konigmatt@googlemail.com", True),
    UserDef("testuser", False, False, False, False),
    UserDef("global", False, False, False, False)]

if __name__ == "__main__":
    print('-'*80)
    print('Creating archives')
    print('-' * 80)
    create_users(user_defs=user_definitions, delete_all=True)
    add_archives_to_database(ARCHIVE_DIRS)
