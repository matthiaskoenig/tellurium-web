from __future__ import absolute_import, print_function, unicode_literals
from django.db import models
from django.core.files import File
from django.apps import apps
from django.utils import timezone
from django.contrib.auth.models import User

from combine import comex

from six import string_types
import os
import hashlib


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


class ArchiveManager(models.Manager):

    def get_or_create(self, *args, **kwargs):
        Tag = apps.get_model("combine", model_name="Tag")
        ArchiveEntry = apps.get_model("combine", model_name="ArchiveEntry")
        ArchiveEntryMeta = apps.get_model("combine", model_name="ArchiveEntryMeta")

        if "archive_path" in kwargs:
            fp=kwargs["archive_path"]
            del kwargs["archive_path"]

            # get or create the archive from hash
            md5 = hash_for_file(fp, hash_type='MD5')
            new_archive, created_a = super(ArchiveManager, self).get_or_create(md5=md5, *args, **kwargs)

            # get name from file path
            name = os.path.basename(fp)
            tokens = name.split(".")
            if len(tokens) > 1:
                name = ".".join(tokens[0:-1])
            new_archive.name = name

            #add file to archive
            with open(fp, 'rb') as f:
                new_archive.file.save(name,File(f))
            new_archive.created = timezone.now()

            # add User to Archive, User format can be string, or User object
            try:
                if isinstance(kwargs['user'], string_types):
                    user = User.objects.get(username=kwargs["user"])
                else:
                    user = kwargs["user"]
            except:
                user = User.objects.get(username="global")
            new_archive.user = user

            #create and add tags to archive
            tags_info = comex.tags_info(fp)
            print(tags_info)
            for tag_info in tags_info:
                tag, created_t = Tag.objects.get_or_create(name=tag_info.name,category=tag_info.category)
                new_archive.tags.add(tag)

            for entry in new_archive.entries():
                entry_dict = {}
                entry_dict["entry"] = entry
                entry_dict["archive"] = new_archive
                new_archive_entry, created_archive_entry = ArchiveEntry.objects.get_or_create(**entry_dict)
                entry_metadata_dic = {"entry":new_archive_entry}
                if "metadata" in entry and isinstance(entry["metadata"],dict):
                    entry_metadata_dic["metadata"]=entry["metadata"]
                ArchiveEntryMeta.objects.get_or_create(**entry_metadata_dic)

            return new_archive, created_a

        else:
            return  super(ArchiveManager, self).get_or_create(*args, **kwargs)


class ArchiveEntryManager(models.Manager):
    def get_or_create(self, *args, **kwargs):
        if "entry" in kwargs:
            entry = kwargs["entry"]
            del kwargs["entry"]

            if not entry["master"]:
                entry["master"] = False

            kwargs["master"] = entry["master"]
            kwargs["format"] = entry["format"]
            kwargs["location"] = entry["location"]

        return super(ArchiveEntryManager, self).get_or_create(*args, **kwargs)




class ArchiveEntryMetaManager(models.Manager):
    def get_or_create(self, *args, **kwargs):

        Creator = apps.get_model("combine", model_name="Creator")
        Date = apps.get_model("combine", model_name="Date")


        if "metadata" in kwargs:
            metadata = kwargs["metadata"]
            del kwargs["metadata"]
            if "description" in metadata:
                kwargs["description"] = metadata["description"]
            kwargs["created"] = metadata["created"]

            archive_entry_meta_new , created_entry_meta = super(ArchiveEntryMetaManager, self).get_or_create(*args, **kwargs)

            for creator in metadata["creators"]:
                creator_dict = {"first_name": creator["givenName"],
                                "last_name":creator["familyName"],
                                "organisation":creator["organisation"],
                                "email": creator["email"]}
                new_creator, _ = Creator.objects.get_or_create(**creator_dict)
                archive_entry_meta_new.creators.add(new_creator)
                new_creator.save()
                archive_entry_meta_new.save()

            for modified in metadata["modified"]:
                modified_new, _ = Date.objects.get_or_create(date=modified)
                archive_entry_meta_new.modified.add(modified_new)
                modified_new.save()
                archive_entry_meta_new.save()




            return archive_entry_meta_new , created_entry_meta


        return super(ArchiveEntryMetaManager, self).get_or_create(*args, **kwargs)


