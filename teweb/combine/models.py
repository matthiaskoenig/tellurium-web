"""
Models definitions.
"""
import logging

import hashlib

from django.db import models
from django.utils import timezone

import libcombine
from celery.result import AsyncResult
from . import comex, validators

logger = logging.getLogger(__name__)


# ===============================================================================
# Utility functions for models
# ===============================================================================

def hash_for_file(filepath, hash_type='MD5', blocksize=65536):
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
        hasher == hashlib.sha1()
    with open(filepath, 'rb') as f:
        buf = f.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(blocksize)
    return hasher.hexdigest()


# ===============================================================================
# Models
# ===============================================================================

class Archive(models.Model):
    """ Combine Archive class.

    Stores the combine archives.
    """
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='archives', validators=[validators.validate_omex])
    created = models.DateTimeField('date published', editable=False)
    md5 = models.CharField(max_length=36)
    task_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ On save, update timestamps. """
        if not self.id:
            self.created = timezone.now()

        if not self.md5:
            self.md5 = hash_for_file(self.file, hash_type='MD5')

            # FIXME: check via hash if the archive is already existing
            # currently duplicate files allowed duplicate archives

        return super(Archive, self).save(*args, **kwargs)

    @property
    def status(self):
        """ Returns the task status of the task.

        :return:
        """
        if self.task_id:
            result = AsyncResult(self.task_id)
            return result.status
        else:
            return None

    def zip_entries(self, as_json=True):
        """ Returns the entries of the combine archive zip file.

        These are all files in the zip files. Not all of these
        have to be managed in the entries of the Combine Archive.

        :param as_json: zip_entries are returned as json
        :return: entries of the zip file
        """

        if as_json:
            # TODO: convert to json
            pass

        import json
        tree_data = [
            {"id": "ajson1", "parent": "#", "text": "Simple root node", "state": {"opened": True, "selected": True}},
            {"id": "ajson2", "parent": "#", "text": "Root node 2", "state": {"opened": True}},
            {"id": "ajson3", "parent": "ajson2", "text": "Child 1"},
            {"id": "ajson4", "parent": "ajson2", "text": "Child 2", "icon": "fa fa-play"}
        ]
        tree_data_json = json.dumps(tree_data)
        return tree_data_json

    def entries(self):
        """ Get entries and omex object from given archive.

        :param archive:
        :return: entries in the combine archive (managed via manifest)
        """
        path = str(self.file.path)

        # read combine archive contents & metadata
        omex = libcombine.CombineArchive()
        if omex.initializeFromArchive(path) is None:
            logger.error("Invalid Combine Archive: {}", self)
            return None

        entries = []
        for i in range(omex.getNumEntries()):
            entry = omex.getEntry(i)
            location = entry.getLocation()
            format = entry.getFormat()

            info = {}
            info['location'] = location
            info['format'] = format
            info['short_format'] = comex.short_format(format)
            info['master'] = entry.getMaster()
            info['metadata'] = comex.metadata_for_location(omex, location=location)

            entries.append(info)

        omex.cleanUp()
        return entries

    def extract_entry(self, index, filename):
        path = str(self.file.path)

        # read combine archive contents & metadata
        omex = libcombine.CombineArchive()
        if omex.initializeFromArchive(path) is None:
            logger.error("Invalid Combine Archive: {}", self)
            return None

        entry = omex.getEntry(index)
        omex.extractEntry(entry.getLocation(), filename)

        omex.cleanUp()

    def get_entry_content(self, index):
        path = str(self.file.path)

        # read combine archive contents & metadata
        omex = libcombine.CombineArchive()
        if omex.initializeFromArchive(path) is None:
            print("Invalid Combine Archive")
            return None
        entry = omex.getEntry(index)
        content = omex.extractEntryToString(entry.getLocation())

        omex.cleanUp()
        return content

# ===============================================================================
# Tag
# ===============================================================================
# TODO: implement
