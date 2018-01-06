"""
Managers for models.
"""
from __future__ import absolute_import, print_function, unicode_literals
import os
import hashlib
import zipfile
import tempfile
import datetime
import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.core.files import File
from django.apps import apps
from django.contrib.auth.models import User
from django.utils.timezone import utc

from .utils.tags import create_tags_for_entry

logger = logging.getLogger(__name__)

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
        # --------------------------
        # Archive
        # --------------------------
        Tag = apps.get_model("combine", model_name="Tag")
        ArchiveEntry = apps.get_model("combine", model_name="ArchiveEntry")
        MetaData = apps.get_model("combine", model_name="MetaData")
        Triple = apps.get_model("combine", model_name="Triple")

        kwargs["created"] = datetime.datetime.now()

        # if string user get the user
        username = kwargs['user']
        if isinstance(username, str):
            kwargs['user'] = User.objects.get(username=username)

        # archive from path
        if "archive_path" in kwargs:
            path = kwargs["archive_path"]
            del kwargs["archive_path"]
            if "name" not in kwargs:
                name = os.path.basename(path)
                kwargs["name"] = os.path.splitext(name)[0]
            kwargs["md5"] = hash_for_file(path, hash_type='MD5')

            # Create archive and store file
            archive = super(ArchiveManager, self).create(*args, **kwargs)
            with open(path, 'rb') as f:
                archive.file.save(name, File(f))

        # archive from file
        else:
            file = kwargs["file"]
            del kwargs["file"]
            hasher = hashlib.md5()
            buf = file.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = file.read(65536)
            kwargs["md5"] = hasher.hexdigest()
            kwargs["name"] = os.path.basename(file.name)
            archive = super(ArchiveManager, self).create(*args, **kwargs)
            archive.file.save(kwargs["name"], File(file))

        archive.save()

        # --------------------------
        # Entries & Metadata
        # --------------------------
        # parse metadata dictionary once
        omex_metadata = archive.omex_metadata()
        with zipfile.ZipFile(archive.path) as z:
            tags = []
            for location, entry in archive.omex_entries().items():
                # --------------------------
                # ArchiveEntry
                # --------------------------
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

                # --------------------------
                # MetaData
                # --------------------------
                # get metadata or create empty metadata
                meta_dict = omex_metadata.get(location,
                              {
                                  'description': None,
                                  'creators': [],
                                  'created': None,
                                  'modified': [],
                                  'bm_triples': [],
                                  'triples': []
                              })

                # set default descriptions
                description = meta_dict["description"]
                if not description:  # this handles None case and empty string
                    base_format = archive_entry.base_format
                    if base_format in ["sed-ml", 'sedml']:
                        description = "SED-ML simulation experiment"
                    elif base_format == "sbml":
                        description = "SBML model"
                    elif base_format == "cellml":
                        description = "CellML model"
                    else:
                        location = archive_entry.location
                        if location == "./manifest.xml":
                            description = "COMBINE archive manifest"
                        if location == "./metadata.rdf":
                            description = "COMBINE archive metadata"
                    meta_dict["description"] = description

                metadata_dict = {"metadata": meta_dict}
                metadata = MetaData.objects.create(**metadata_dict)
                archive_entry.metadata = metadata
                # don't forget to save the entry
                archive_entry.save()

                # ----------------------------
                # additional metadata entries
                # ----------------------------
                if archive_entry.base_format == "sbml":
                    logger.info("Adding SBML external annotations")

                    # externalize annotations
                    from combine.metadata import sbml as mdsbml
                    mdsbml_dict = mdsbml.parse_metadata(path_sbml=archive_entry.path, prefix=location)

                    # add triples
                    entry_meta = archive_entry.metadata
                    triples = []
                    for sbml_location, sbml_dict in mdsbml_dict.items():
                        metadata_triples = sbml_dict.get('bm_triples')
                        for (s, s_type, p, p_type, o, o_type) in metadata_triples:
                            triple = Triple.objects.create(subject=s, subject_type=s_type,
                                                           predicate=p, predicate_type=p_type,
                                                           object=o, object_type=o_type)
                            triples.append(triple)

                        entry_meta.triples.add(*triples)
                        entry_meta.save()
                    archive_entry.save()

                # ----------------------
                # Tags from given entry
                # ----------------------

                # FIXME: this must be done on save method of entry (dynamic update of tags if entries change)
                tags_info = create_tags_for_entry(archive_entry)
                # pprint(tags_info)
                for tag_info in tags_info:
                    tag, created_tag = Tag.objects.get_or_create(name=tag_info.name, category=tag_info.category)
                    tags.append(tag)

        # add collected tags
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

            # make sure the date string is parsable
            created = metadata.get("created")
            if created:
                # check that parsable
                try:
                    date = Date.objects.create(date=created)
                except ValidationError:
                    logger.error("Created date is not valid '{}', probably incorrect RDF.".format(created))
                    created = None

            # set default created date
            if created is None:
                now = datetime.datetime.utcnow().replace(tzinfo=utc)
                created = now
                metadata.get('modified').append(now)
            kwargs["created"] = created

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
                try:
                    date = Date.objects.create(date=modified_date)
                    modified.append(date)
                except ValidationError:
                    logger.error("Modifed date is not valid '{}', probably incorrect RDF.".format(modified_date))

            entry_meta.modified.add(*modified)

            # add triples
            triples = []
            for metadata_triples in [metadata["bm_triples"], metadata["triples"]]:
                for (s, s_type, p, p_type, o, o_type) in metadata_triples:
                    triple = Triple.objects.create(subject=s, subject_type=s_type,
                                                   predicate=p, predicate_type=p_type,
                                                   object=o, object_type=o_type)
                    triples.append(triple)

            entry_meta.triples.add(*triples)
            entry_meta.save()

            return entry_meta

        else:
            return super(MetaDataManager, self).create(*args, **kwargs)
