"""
Data and helper functions for filling the database.
"""

import os
from collections import namedtuple
import time

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from combine.models import Archive, Tag
from . import comex


UserDef = namedtuple('UserDef', ['username', 'first_name', 'last_name', 'email', 'superuser'])


def add_archives_to_database(archive_dirs, debug=False):
    """ Add archives to database from given directories.

    :param archive_dirs:
    :return:
    """
    # list files
    omex_files = comex.get_archive_paths(archive_dirs)

    for path in sorted(omex_files):
        if debug:
            print(os.path.relpath(path, os.getcwd()))

        start_time = time.time()

        # default user is "global" but can be changed by adding user= < User Object >, user = User.username( string)

        #Archive.objects.create(file=open(path, 'rb'))

        _, created = Archive.objects.get_or_create(archive_path=path)

        if not created:
            print("Archive already exists, not recreated: {}".format(path))

        if debug:
            print("\t{:2.2f} [s]".format(time.time() - start_time))


def create_users(user_defs, delete_all=True, debug=False):
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
                                                 password=os.environ['DJANGO_ADMIN_PASSWORD'])
        else:
            user = User.objects.create_user(username=user_def.username, email=user_def.email,
                                            password=os.environ['DJANGO_ADMIN_PASSWORD'])
        user.last_name = user_def.last_name
        user.first_name = user_def.first_name
        user.save()

    # display users
    if debug:
        for user in User.objects.all():
            print('\t', user.username, user.email, user.password)
