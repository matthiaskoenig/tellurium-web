"""
Data and helper functions for filling the database.
"""

import os
from collections import namedtuple
import time

from django.contrib.auth.models import  Group
from guardian.compat import get_user_model

from guardian.shortcuts import get_anonymous_user


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

        archive = Archive.objects.create(archive_path=path, user="global", global_archive=True)

        if debug:
            print("\t{:2.2f} [s]".format(time.time() - start_time))


def create_users(user_defs, delete_all=True, debug=False):
    """ Create users in database from user definitions.

    :param delete_all: deletes all existing users
    :return:
    """
    # adds user to database
    normal_group = Group.objects.create(name='normal_group')
    # anon = get_anonymous_user()
    User = get_user_model()
    anon = User.get_anonymous()
    anon.groups.add(normal_group)

    if not user_defs:
        user_defs = []

    # deletes all users
    if delete_all:
        User.objects.all().delete()


    for user_def in user_defs:
        if user_def.superuser:
            user = User.objects.create_superuser(username=user_def.username, email=user_def.email,
                                                 password=os.environ['DJANGO_ADMIN_PASSWORD'])
        else:
            user = User.objects.create_user(username=user_def.username, email=user_def.email,
                                            password=os.environ['DJANGO_ADMIN_PASSWORD'])
            user.groups.add(normal_group)
        user.last_name = user_def.last_name
        user.first_name = user_def.first_name
        user.save()

    # display users
    if debug:
        for user in User.objects.all():
            print('\t', user.username, user.email, user.password)
