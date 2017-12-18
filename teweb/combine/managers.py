"""
Managers for models.
"""
from __future__ import absolute_import, print_function, unicode_literals
import os
import hashlib
from six import string_types

from django.db import models
from django.core.files import File
from django.apps import apps
from django.utils import timezone
from django.contrib.auth.models import User

from .tags import create_tags_for_archive


# ===============================================================================
# Utility functions for models
# ===============================================================================
def hash_for_file(file, hash_type='MD5', blocksize=65536):
    """ Calculate the md5_hash for a file.

        Calculating a hash for a file is always useful when you need to check if two files
        are identical, or to make sure that the contents of a file were not changed, and to
        check the integrity of a file when it is transmitted over a network.
        he most used algorithms to hash a file are MD5 and SHA-1. They are used because they
        are fast and they provide a good way to identify different files.
        [http://www.pythoncentral.io/hashing-files-with-python/]
    """
    hasher = None
    if hash_type == 'MD5':
        hasher = hashlib.md5()
    elif hash_type == 'SHA1':
        hasher = hashlib.sha1()

    with open(file, 'rb') as f:
        buf = f.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(blocksize)
    return hasher.hexdigest()


# ===============================================================================
# Manager
# ===============================================================================
class ArchiveManager(models.Manager):
    """ Manager for Archive. """

    def get_or_create(self, *args, **kwargs):
        """ Function creating all the archive information from given file.
        This is the main entry point for import of archives.
        """

        # get models
        Tag = apps.get_model("combine", model_name="Tag")
        ArchiveEntry = apps.get_model("combine", model_name="ArchiveEntry")
        MetaData = apps.get_model("combine", model_name="MetaData")

        if "archive_path" in kwargs:
            path = kwargs["archive_path"]
            del kwargs["archive_path"]

            # get or create the archive (uniqueness based on hash)
            md5 = hash_for_file(path, hash_type='MD5')
            archive, created_archive = super(ArchiveManager, self).get_or_create(md5=md5, *args, **kwargs)

            # get name without extension
            name = os.path.basename(path)
            archive.name = os.path.splitext(name)[0]

            # store combine archive as file
            with open(path, 'rb') as f:
                archive.file.save(name, File(f))

            # FIXME: unclear where to do this (in save, create?)
            archive.created = timezone.now()

            # add User to Archive, User format can be string, or User object
            try:
                if isinstance(kwargs['user'], string_types):
                    user = User.objects.get(username=kwargs["user"])
                elif isinstance(kwargs['user'], User):
                    user = kwargs["user"]
            except KeyError:
                user = User.objects.get(username="global")
            archive.user = user
            archive.save()

            # create tags for archive
            tags_info = create_tags_for_archive(path)
            for tag_info in tags_info:
                tag, created_tag = Tag.objects.get_or_create(name=tag_info.name, category=tag_info.category)
                archive.tags.add(tag)

            # metadata parsed from archive (lookup via locations)
            omex_metadata = archive.omex_metadata()

            # create entries for files listed in the OMEX manifest.xml
            for location, entry in archive.omex_entries().items():
                print("this si the archive:",entry)
                print("archive:", archive)
                entry_dict = {
                    "entry": entry,
                    "archive": archive,
                }
                archive_entry, _ = ArchiveEntry.objects.get_or_create(**entry_dict)
                archive_entry.save()

                # create single metadata for every entry
                meta_dict = omex_metadata.get(location)
                print(location)
                if meta_dict:
                    print(meta_dict['about'])
                else:
                    print("No metadata information")
                print("\n")
                if meta_dict:

                    metadata_dict = {
                        "metadata": meta_dict,
                    }
                    metadata, _ = MetaData.objects.create(**metadata_dict)
                    archive_entry.metadata = metadata

                    metadata.save()

                archive_entry.save()

            # add the additional entries from the zip content
            # TODO: implement, see https://github.com/matthiaskoenig/tellurium-web/issues/73

            return archive, created_archive

        else:
            return super(ArchiveManager, self).get_or_create(*args, **kwargs)


class ArchiveEntryManager(models.Manager):
    """ Manager for ArchiveEntry. """

    def get_or_create(self, *args, **kwargs):
        entry = kwargs.get("entry")
        if entry:
            # fields required to generate ArchiveEntry
            del kwargs["entry"]
            kwargs["master"] = entry["master"]
            kwargs["format"] = entry["format"]
            kwargs["location"] = entry["location"]


        return super(ArchiveEntryManager, self).get_or_create(*args, **kwargs)


class MetaDataManager(models.Manager):
    """ Manager for ArchiveEntryMeta. """

    def create(self, *args, **kwargs):
        #Creator = apps.get_model("combine", model_name="Creator")
        #Date = apps.get_model("combine", model_name="Date")

        metadata = kwargs.get("metadata")
        from pprint import pprint
        pprint(metadata)

        if metadata:
            # fields required to generate ArchiveEntryMeta
            del kwargs["metadata"]
            if "description" in metadata:
                kwargs["description"] = metadata.get("description")
            kwargs["created"] = metadata.get("created")

            # create initial meta entry
            entry_meta, created_meta = super(MetaDataManager, self).get_or_create(*args, **kwargs)
            # entry_meta, created_meta = super(MetaDataManager, self).create(*args, **kwargs)

            # add creator information
            for creator_info in metadata.get("creators", []):
                creator_dict = {
                    "first_name": creator_info.get("givenName"),
                    "last_name": creator_info.get("familyName"),
                    "organisation": creator_info.get("organisation"),
                    "email": creator_info.get("email"),
                }
                entry_meta.creators.create(**creator_dict)
                #entry_meta.creators.add(creator)
                entry_meta.save()
                #creator.save()

            # add modified stamps
            for modified_date in metadata.get("modified", []):
                #modified = Date.objects.create(date=modified_date)
                entry_meta.modified.create(date=modified_date)
                #modified.save()
                entry_meta.save()

            return entry_meta, created_meta

        else:
            return super(MetaDataManager, self).create(*args, **kwargs)
