"""
Data and helper functions for filling the database.
"""

import os
from collections import namedtuple

from django.core.files import File
from django.contrib.auth.models import User

from combine.models import Archive, Tag, hash_for_file
from combine import comex

UserDef = namedtuple('UserDef', ['username', 'first_name', 'last_name', 'email', 'superuser'])


def add_archives_to_database(archive_dirs):
    """ Add archives to database from given directories.

    :param archive_dirs:
    :return:
    """
    # list files
    omex_files = comex.get_omex_file_paths(archive_dirs)

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
            tokens = name.split(".")
            if len(tokens) > 1:
                name = ".".join(tokens[0:-1])

            django_file = File(open(f, 'rb'))
            new_archive = Archive(name=name)
            global_user = User.objects.get(username="global")
            new_archive.user = global_user
            new_archive.file.save(name, django_file, save=False)
            new_archive.md5 = hash_for_file(f, hash_type='MD5')
            new_archive.full_clean()
            new_archive.save()

            # create tag info
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
                                                 password=os.environ['DJANGO_ADMIN_PASSWORD'])
        else:
            user = User.objects.create_user(username=user_def.username, email=user_def.email,
                                            password=os.environ['DJANGO_ADMIN_PASSWORD'])
        user.last_name = user_def.last_name
        user.first_name = user_def.first_name
        user.save()

    # display users
    for user in User.objects.all():
        print('\t', user.username, user.email, user.password)
