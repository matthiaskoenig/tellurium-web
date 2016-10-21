from __future__ import print_function, division
import os
import sys
sys.path.append("/home/mkoenig/git/tellurium-web/teweb")
print(sys.path)
import django
django.setup()
from combine.models import Archive

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

    django.setup()
    print('-'*80)
    print('Creating archives')
    print('-' * 80)
    add_archives_to_database()
