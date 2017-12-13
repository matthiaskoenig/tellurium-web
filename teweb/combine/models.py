"""
Models definitions.
"""
import uuid as uuid_lib

import logging

from django.db import models
from django.utils import timezone
from djchoices import DjangoChoices, ChoiceItem
from django.contrib.auth.models import User

from celery.result import AsyncResult

try:
    import libcombine
except ImportError:
    import tecombine as libcombine
from celery.result import AsyncResult
from . import comex, validators

from combine.managers import ArchiveManager, ArchiveEntryManager, ArchiveEntryMetaManager, hash_for_file


logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 500




# ===============================================================================
# Models
# ===============================================================================

class TagCategory(DjangoChoices):
    format = ChoiceItem("format")
    source = ChoiceItem("source")
    simulation = ChoiceItem("sim")
    model = ChoiceItem("model")
    sedml = ChoiceItem("sedml")
    misc = ChoiceItem("misc")


class Tag(models.Model):
    """ Tag class to describe content of files or archives. """

    name = models.CharField(max_length=MAX_TEXT_LENGTH)
    category = models.CharField(max_length=MAX_TEXT_LENGTH, choices=TagCategory.choices)
    uuid = models.UUIDField(  # Used by the API to look up the record
                            db_index=True,
                            default=uuid_lib.uuid4,
                            editable=False)

    def __str__(self):
        return self.name

    #@property
    #def uuid(self):
    #    return "-".join([self.category, self.name])

    class Meta:
        unique_together = ('category', 'name')


class Archive(models.Model):
    """ COMBINE Archive class.

    Stores the combine archives.

    self.file: stores the original uploaded archive without any modifications.
        All modifications are stored in the additional models like ArchiveEntry and ArchiveEntryMeta.
    """
    name = models.CharField(max_length=MAX_TEXT_LENGTH)
    file = models.FileField(upload_to='archives', validators=[validators.validate_omex])
    created = models.DateTimeField('date published', editable=False)
    md5 = models.CharField(max_length=36, blank=True)
    task_id = models.CharField(max_length=100, blank=True)
    tags = models.ManyToManyField(Tag, related_name="archives")
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    uuid = models.UUIDField(  # Used by the API to look up the record

        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    objects = ArchiveManager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ On save, update timestamps. """
        if not self.id:
            self.created = timezone.now()

        if not self.md5:
            self.md5 = hash_for_file(self.file, hash_type='MD5')

        return super(Archive, self).save(*args, **kwargs)

    @property
    def md5_short(self):
        return self.md5[0:8]

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

    @property
    def path(self):
        return str(self.file.path)

    @property
    def task(self):
        task = None
        if self.task_id:
            task = AsyncResult(self.task_id)
        return task

    def omex(self):
        """ Open CombineArchive for given archive.

        Don't forget to close the omex after using it.
        :return:
        """
        omex = libcombine.CombineArchive()
        if omex.initializeFromArchive(self.path) is None:
            logger.error("Invalid Combine Archive: {}", self)
            return None
        return omex

    def entries(self):
        """ Get entries and omex object from given archive.

        :return: entries in the combine archive (managed via manifest)
        """
        return comex.entries_info(self.path)

    def extract_entry_by_index(self, index, filename):
        """ Extracts entry at index to filename.

        :param index:
        :param filename:
        :return:
        """
        omex = self.omex()
        entry = omex.getEntry(index)
        omex.extractEntry(entry.getLocation(), filename)
        omex.cleanUp()

    def extract_entry_by_location(self, location, filename):
        """ Extracts entry at location to filename.

        :param location:
        :param filename:
        :return:
        """
        omex = self.omex()
        entry = omex.getEntryByLocation(location)
        omex.extractEntry(location, filename)
        omex.cleanUp()

    def entry_content_by_index(self, index):
        """ Extracts entry content at given index.

        :param index: index of entry
        :return: content
        """
        omex = self.omex()
        entry = omex.getEntry(index)
        content = omex.extractEntryToString(entry.getLocation())
        omex.cleanUp()
        return content

    def entry_content_by_location(self, location):
        """ Extracts entry content at given location.

        :param location: location of entry
        :return: content
        """
        omex = self.omex()
        entry = omex.getEntryByLocation(location)
        content = omex.extractEntryToString(entry.getLocation())
        omex.cleanUp()
        return content

    def zip_entries(self):
        """ Returns the entries of the combine archive zip file.

        :return: entries of the zip file
        """
        return comex.zip_tree_content(self.path)

########################################
# RDF information
########################################
#
# http://co.mbine.org/standards/qualifiers

MODEL_QUALIFIER_PREFIX = "http://biomodels.net/model-qualifiers/"
BIOLOGICAL_QUALIFIER_PREFIX = "http://biomodels.net/biological-qualifiers/"

# TODO: fill up the information from http://co.mbine.org/standards/qualifiers
ModelQualifierType = {
    "is": [0, "identity", "The modelling object represented by the model element is identical with the subject of the referenced resource (modelling object B). For instance, this qualifier might be used to link an encoded model to a database of models."],
    "isDescribedBy": 1,
    "isDerivedFrom": 2,
    "isInstanceOf": 3,
    "hasInstance": 4,
}

BiologicalQualifierType = {
    "is": 0,
    "hasPart": 1,
    "isPartOf": 2,
    "isVersionOf": 3,
    "hasVersion": 4,
    "isHomologTo": 5,
    "isDescribedBy": 6,
    "isEncodedBy": 7,
    "encodes": 8,
    "occursIn": 9,
    "hasProperty": 10,
    "isPropertyOf": 11,
    "hasTaxon": 12,
}


class Date(models.Model):
    date = models.DateTimeField()


class Creator(models.Model):
    first_name = models.CharField(max_length=MAX_TEXT_LENGTH)
    last_name = models.CharField(max_length=MAX_TEXT_LENGTH)
    organisation = models.CharField(max_length=MAX_TEXT_LENGTH, blank=True, null=True)
    email = models.EmailField(max_length=MAX_TEXT_LENGTH, blank=True, null=True)



class Triple(models.Model):
    subject = models.TextField()
    predicate = models.TextField()
    object = models.TextField()

    # TODO: We want subset of biomodels triples
    # TODO: get list of biomodels qualifiers


# TODO: store the actual file for the entry (use archive and location to store the file)
#   FileField

class ArchiveEntry(models.Model):
    """ Entry information.
    This is the content of the manifest file.
    """
    archive = models.ForeignKey(Archive, on_delete=models.CASCADE)
    location = models.CharField(max_length=MAX_TEXT_LENGTH)
    format = models.CharField(max_length=MAX_TEXT_LENGTH)
    master = models.BooleanField(default=False)

    objects = ArchiveEntryManager()





class ArchiveEntryMeta(models.Model):
    """ Metadata for given Archive entry.

     From this information the metadata.rdf file for the archive can be generated.
     """
    entry = models.OneToOneField(ArchiveEntry, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    creators = models.ManyToManyField(Creator)
    created = models.DateTimeField(editable=False,null=True, blank=True)
    modified = models.ManyToManyField(Date)
    triples = models.ManyToManyField(Triple)

    objects = ArchiveEntryMetaManager()



