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

# add combine directory for imports
FILE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
PROJECT_DIR = os.path.join(FILE_DIR, "../teweb/")
sys.path.append(PROJECT_DIR)

# setup django
from combine.utils import django_setup

from combine.utils.data import UserDef, create_users, add_archives_to_database
from combine.fixtures.users import user_defs

# directories with OMEX archives
ARCHIVE_DIRS = [
    os.path.join(FILE_DIR, "../archives"),
    # os.path.join(FILE_DIR, "../archives/annotation"),
    # os.path.join(FILE_DIR, "../../sedml-test-suite/archives"),
    # os.path.join(FILE_DIR, "../../sedml-test-suite/archives/biomodels"),
    # os.path.join(FILE_DIR, "../../sedml-test-suite/archives/jws"),
    # os.path.join(FILE_DIR, "../../sedml-test-suite/archives/sedml-L1V3/"),
    # os.path.join(FILE_DIR, "../../sed-ml/specification/level-1-version-3/examples/__omex__"),
]

if __name__ == "__main__":
    print('-'*80)
    print('Creating archives')
    print('-' * 80)
    create_users(user_defs=user_defs, delete_all=True)
    add_archives_to_database(ARCHIVE_DIRS, debug=True)
