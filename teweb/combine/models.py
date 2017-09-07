"""
Models.
"""

from __future__ import absolute_import, print_function, unicode_literals

import hashlib

from django.db import models
from django.utils import timezone
from django.core.validators import ValidationError
try:
    import libcombine
except ImportError:
    import tecombine as libcombine
import libsedml

from celery.result import AsyncResult


# ===============================================================================
# Utility functions for models
# ===============================================================================
def validate_omex(fieldFile):
    """ Validator for the omex file.
    Necessary to run basic file checks on upload.
    Otherwise the archives will create problems on execution.

    :param fieldFile:
    :return:
    """

    print('*'*80)
    print(fieldFile)
    print(type(fieldFile))
    print('*' * 80)

    # check that it is a jar file
    path = fieldFile.path
    print(path)
    file = fieldFile.path
    print(file)

    # omex = tecombine.OpenCombine(path)
    # omex.listContents()

    # FIXME: currently not completely implemented.

    """
    # libcombine
    # Try to read the archive
    omex = libcombine.CombineArchive()
    if not omex.initializeFromArchive(path):
        print("Invalid Combine Archive")
        raise ValidationError(
            _('Invalid archive: %(file)s'),
            code='invalid',
            params={'file': 'file'},
        )
    """


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
# Archive
# ===============================================================================

class Archive(models.Model):
    """ Combine Archive class. """
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='archives', validators=[validate_omex])
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
            # the file is uploaded at this point
            # file_path = str(self.file.path)
            self.md5 = hash_for_file(self.file, hash_type='MD5')

            # check via hash if the archive is already existing
            # not really necessary, we allow for duplicate archives

        return super(Archive, self).save(*args, **kwargs)

    @property
    def status(self):
        if self.task_id:
            result = AsyncResult(self.task_id)
            return result.status
        else:
            return None

    def get_entries(self):
        """ Get entries and omex object from given archive.

        :param archive:
        :return:
        """
        path = str(self.file.path)

        # read combine archive contents & metadata
        omex = libcombine.CombineArchive()
        if omex.initializeFromArchive(path) is None:
            print("Invalid Combine Archive")
            return None

        entries = []
        for i in range(omex.getNumEntries()):
            entry = omex.getEntry(i)
            # entry.getLocation(), entry.getFormat()
            # TODO: IMPLEMENT ME
            # printMetaDataFor(archive, entry.getLocation());

            # ! hardcopy the required information so archive can be closed again.
            info = {}
            info['location'] = entry.getLocation()
            info['format'] = entry.getFormat()


            entries.append(info)


            # the entry could now be extracted via
            # archive.extractEntry(entry.getLocation(), <filename or folder>)

            # or used as string
            # content = archive.extractEntryToString(entry.getLocation());

        omex.cleanUp()

        return omex, entries

# ===============================================================================
# Tag
# ===============================================================================
# TODO: implement
