"""
Managers for models.
"""
from __future__ import absolute_import, print_function, unicode_literals
import os
import hashlib
from six import string_types
import zipfile
import tempfile
import datetime

from pprint import pprint

from django.db import models
from django.core.files import File
from django.apps import apps
from django.contrib.auth.models import User
from django.utils.timezone import utc

from .utils.tags import create_tags_for_entry


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

    def create(self, *args, **kwargs):
        Tag = apps.get_model("combine", model_name="Tag")
        ArchiveEntry = apps.get_model("combine", model_name="ArchiveEntry")
        MetaData = apps.get_model("combine", model_name="MetaData")


        kwargs["created"] = datetime.datetime.now()
        file= kwargs["file"]
        #kwargs["file"] = File(kwargs["file"])
        del kwargs["file"]
        hasher = hashlib.md5()
        buf = file.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = file.read(65536)
        kwargs["md5"] = hasher.hexdigest()
        kwargs["name"] = os.path.basename(file.name)
        archive = super(ArchiveManager, self).create(*args, **kwargs)

        archive.file.save(kwargs["name"],File(file))

        try:
            if isinstance(kwargs['user'], string_types):
                archive.user = User.objects.get(username=kwargs["user"])
            elif isinstance(kwargs['user'], User):
                archive.user = kwargs["user"]
        except KeyError:
            archive.user = User.objects.get(username="global")

        archive.save()

        # only parse this once !
        metadata_dict = archive.omex_metadata()

        with zipfile.ZipFile(file) as z:

            tags = []

            for location, entry in archive.omex_entries().items():
                entry_dict = {
                    "entry": entry,
                    "archive": archive,
                }
                archive_entry, _ = ArchiveEntry.objects.get_or_create(**entry_dict)

                # add file to archive entry
                if location != ".":
                    zip_name = location.replace("./", "")

                    # extract to temporary file
                    suffix = location.split('/')[-1]
                    tmp = tempfile.NamedTemporaryFile("wb", suffix=suffix)
                    tmp.write(z.read(zip_name))
                    tmp.seek(0)  # rewind file for reading !

                    with open(tmp.name, 'rb') as f:
                        name = zip_name
                        # name = name.replace("/", '__')
                        archive_entry.file.save(name, File(f))
                    tmp.close()

                # create metadata for entry
                meta_dict = metadata_dict.get(location)
                if meta_dict.get("created") is None:
                    # dummy created timestamp
                    now = datetime.datetime.utcnow().replace(tzinfo=utc)
                    meta_dict['created'] = now
                    meta_dict['modified'].append(now)

                metadata_dict = {
                    "metadata": meta_dict,
                }
                metadata = MetaData.objects.create(**metadata_dict)

                archive_entry.metadata = metadata
                archive_entry.save()

                # add some standard descriptions
                if (metadata.description is None) or (len(metadata.description) == 0):
                    base_format = archive_entry.base_format
                    if base_format in ["sed-ml", 'sedml']:
                        metadata.description = "SED-ML simulation experiment"
                        metadata.save()
                    elif base_format == "sbml":
                        metadata.description = "SBML model"
                        metadata.save()
                    elif base_format == "cellml":
                        metadata.description = "CellML model"
                        metadata.save()
                    location = archive_entry.location
                    if location == "./manifest.xml":
                        metadata.description = "COMBINE archive manifest"
                        metadata.save()
                    if location == "./metadata.rdf":
                        metadata.description = "COMBINE archive metadata"
                        metadata.save()

                # Tags from given entry
                # FIXME: this must be done on save method of entry (dynamic update of tags if entries change)
                tags_info = create_tags_for_entry(archive_entry)
                # pprint(tags_info)
                for tag_info in tags_info:
                    tag, created_tag = Tag.objects.get_or_create(name=tag_info.name, category=tag_info.category)
                    tags.append(tag)

            # add all tags at once
            archive.tags.add(*tags)
            archive.save()

            # update the manifest
            archive.update_manifest_entry()

            # update the metadata
            archive.update_metadata_entry()


        return archive


    def get_or_create(self, *args, **kwargs):
        """ Create archive information from given archive file.
        This is the main entry point for the import of archives in the database.
        """
        # get models
        Tag = apps.get_model("combine", model_name="Tag")
        ArchiveEntry = apps.get_model("combine", model_name="ArchiveEntry")
        MetaData = apps.get_model("combine", model_name="MetaData")

        if "archive_path" in kwargs:

            # ----------------------------
            # Create archive
            # ----------------------------
            path = kwargs["archive_path"]
            del kwargs["archive_path"]

            # get or create the archive (uniqueness based on hash)
            md5 = hash_for_file(path, hash_type='MD5')
            if not "user" in kwargs:
                kwargs["user__isnull"] = True

            archive, created_archive = super(ArchiveManager, self).get_or_create(md5=md5, *args, **kwargs)

            # get name without extension
            name = os.path.basename(path)
            archive.name = os.path.splitext(name)[0]

            # store combine archive as file
            with open(path, 'rb') as f:
                archive.file.save(name, File(f))

            # add User to Archive, User format can be string, or User object
            try:
                if isinstance(kwargs['user'], string_types):
                    archive.user = User.objects.get(username=kwargs["user"])
                elif isinstance(kwargs['user'], User):
                    archive.user = kwargs["user"]
            except KeyError:
                archive.user = User.objects.get(username="global")

            archive.save()

            # ----------------------------
            # Parse metadata
            # ----------------------------
            # metadata parsed from archive (lookup via locations)
            omex_metadata = archive.omex_metadata()

            # ----------------------------
            # Create ArchiveEntries
            # ----------------------------
            with zipfile.ZipFile(path) as z:

                tags = []

                for location, entry in archive.omex_entries().items():
                    entry_dict = {
                        "entry": entry,
                        "archive": archive,
                    }
                    archive_entry, _ = ArchiveEntry.objects.get_or_create(**entry_dict)

                    # add file to archive entry
                    if location != ".":
                        zip_name = location.replace("./", "")

                        # extract to temporary file
                        suffix = location.split('/')[-1]
                        tmp = tempfile.NamedTemporaryFile("wb", suffix=suffix)
                        tmp.write(z.read(zip_name))
                        tmp.seek(0)  # rewind file for reading !

                        with open(tmp.name, 'rb') as f:
                            name = zip_name
                            # name = name.replace("/", '__')
                            archive_entry.file.save(name, File(f))
                        tmp.close()

                    # create metadata for entry
                    meta_dict = omex_metadata.get(location)
                    if meta_dict.get("created") is None:
                        # dummy created timestamp
                        now = datetime.datetime.utcnow().replace(tzinfo=utc)
                        meta_dict['created'] = now
                        meta_dict['modified'].append(now)

                    metadata_dict = {
                        "metadata": meta_dict,
                    }
                    metadata = MetaData.objects.create(**metadata_dict)

                    archive_entry.metadata = metadata
                    archive_entry.save()

                    # add some standard descriptions
                    if (metadata.description is None) or (len(metadata.description) == 0):
                        base_format = archive_entry.base_format
                        if base_format in ["sed-ml", 'sedml']:
                            metadata.description = "SED-ML simulation experiment"
                            metadata.save()
                        elif base_format == "sbml":
                            metadata.description = "SBML model"
                            metadata.save()
                        elif base_format == "cellml":
                            metadata.description = "CellML model"
                            metadata.save()
                        location = archive_entry.location
                        if location == "./manifest.xml":
                            metadata.description = "COMBINE archive manifest"
                            metadata.save()
                        if location == "./metadata.rdf":
                            metadata.description = "COMBINE archive metadata"
                            metadata.save()

                # Tags from given entry
                    # FIXME: this must be done on save method of entry (dynamic update of tags if entries change)
                    tags_info = create_tags_for_entry(archive_entry)
                    # pprint(tags_info)
                    for tag_info in tags_info:
                        tag, created_tag = Tag.objects.get_or_create(name=tag_info.name, category=tag_info.category)
                        tags.append(tag)

                # add all tags at once
                archive.tags.add(*tags)
                archive.save()

                # update the manifest
                archive.update_manifest_entry()

                # update the metadata
                archive.update_metadata_entry()

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

        Date = apps.get_model("combine", model_name="Date")
        Creator = apps.get_model("combine", model_name="Creator")
        Triple = apps.get_model("combine", model_name="Triple")

        metadata = kwargs.get("metadata")

        if metadata:
            # fields required to generate ArchiveEntryMeta
            del kwargs["metadata"]
            if "description" in metadata:
                kwargs["description"] = metadata.get("description")
            kwargs["created"] = metadata.get("created")

            # create initial meta entry
            entry_meta = super(MetaDataManager, self).create(*args, **kwargs)

            # add creators
            creators = []
            for creator_info in metadata.get("creators", []):
                creator_dict = {
                    "first_name": creator_info.get("givenName"),
                    "last_name": creator_info.get("familyName"),
                    "organisation": creator_info.get("organisation"),
                    "email": creator_info.get("email"),
                }
                creators.append(
                    Creator.objects.create(**creator_dict)
                )
            entry_meta.creators.add(*creators)

            # add modified time stamps
            modified = []
            for modified_date in metadata.get("modified", []):
                modified.append(
                    Date.objects.create(date=modified_date)
                )
            entry_meta.modified.add(*modified)

            # add triples
            triples = []
            # add remaining triples, everything which could not be parsed
            for (s, s_type, p, p_type, o, o_type) in metadata["bm_triples"]:
                triple = Triple.objects.create(subject=s, subject_type=s_type,
                                               predicate=p, predicate_type=p_type,
                                               object=o, object_type=o_type)
                triples.append(triple)

            # add remaining triples, everything which could not be parsed
            for (s, s_type, p, p_type, o, o_type) in metadata["triples"]:
                triple = Triple.objects.create(subject=s, subject_type=s_type,
                                               predicate=p, predicate_type=p_type,
                                               object=o, object_type=o_type)
                triples.append(triple)


            entry_meta.triples.add(*triples)

            # save the entry
            entry_meta.save()

            return entry_meta

        else:
            return super(MetaDataManager, self).create(*args, **kwargs)
