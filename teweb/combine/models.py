"""
Models definitions.
"""
import uuid as uuid_lib
import logging

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.contrib.auth.models import User
from djchoices import DjangoChoices, ChoiceItem
from celery.result import AsyncResult

try:
    import libcombine
except ImportError:
    import tecombine as libcombine

from . import comex, validators

from combine.managers import ArchiveManager, ArchiveEntryManager, MetaDataManager, hash_for_file
logger = logging.getLogger(__name__)

# ===============================================================================
# Settings
# ===============================================================================
MAX_TEXT_LENGTH = 500


# ===============================================================================
# Archives
# ===============================================================================
class TagCategory(DjangoChoices):
    """ Categories for the tags. """
    format = ChoiceItem("format")
    source = ChoiceItem("source")
    simulation = ChoiceItem("sim")
    model = ChoiceItem("model")
    sedml = ChoiceItem("sedml")
    misc = ChoiceItem("misc")


class Tag(models.Model):
    """ Tag class to describe content of archives.

    Archives can have associated tags describing the general content of the archive
    and key files in the archive, e.g., content of SBML or SED-ML files.
    """
    name = models.CharField(max_length=MAX_TEXT_LENGTH)
    category = models.CharField(max_length=MAX_TEXT_LENGTH, choices=TagCategory.choices)
    uuid = models.UUIDField(  # Used by the API to look up the record
                            db_index=True,
                            default=uuid_lib.uuid4,
                            editable=False)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('category', 'name')


class Archive(models.Model):
    """ COMBINE Archive class.

    The individual file entries are stored in the ArchiveEntries, the MetaData in the associated MetaData.

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

    @property
    def description(self):
        """ Get description from the metadata of top level entry."""
        description = ""
        try:
            entry = self.entries.get(location=".")
            metadata = entry.metadata
            if metadata and metadata.description:
                description = metadata.description
        except ObjectDoesNotExist:
            pass
        return description

    def omex_entries(self):
        """ Get entries and omex object from given archive.

        :return: entries in the combine archive (managed via manifest)
        """
        return comex.entries_info(self.path)

    def zip_entries(self):
        """ Returns the entries of the combine archive zip file.
        This is the basis of creating the tree.

        :return: entries of the zip file
        """
        return comex.zip_tree_content(self.path)

    def has_entries(self):
        """ Check if ArchiveEntries exist for archive. """
        return self.entries.count() > 0



# TODO: store the actual file for the entry (use archive and location to store the file), use a FileField
class ArchiveEntry(models.Model):
    """ Entry information.
    This is the content of the manifest file.
    """

    archive = models.ForeignKey(Archive, on_delete=models.CASCADE, related_name="entries")
    location = models.CharField(max_length=MAX_TEXT_LENGTH)
    format = models.CharField(max_length=MAX_TEXT_LENGTH)
    master = models.BooleanField(default=False)
    metadata = models.ForeignKey("MetaData", on_delete=models.SET_NULL, null=True)

    objects = ArchiveEntryManager()

    def __str__(self):
        return "<ArchiveEntry: {}|{}>".format(self.archive, self.location)

    class Meta:
        verbose_name_plural = "archive entries"

    @property
    def short_format(self):
        return comex.short_format(self.format)

    @property
    def base_format(self):
        return comex.base_format(self.format)


########################################
# RDF information
########################################
# This is all the content of the metadata files.
class Date(models.Model):
    date = models.DateTimeField()


class Creator(models.Model):
    """ RDF creator of archive entry. """
    first_name = models.CharField(max_length=MAX_TEXT_LENGTH)
    last_name = models.CharField(max_length=MAX_TEXT_LENGTH)
    organisation = models.CharField(max_length=MAX_TEXT_LENGTH, blank=True, null=True)
    email = models.EmailField(max_length=MAX_TEXT_LENGTH, blank=True, null=True)


class Triple(models.Model):
    subject = models.TextField()
    predicate = models.TextField()
    object = models.TextField()

    # TODO: We want subset of biomodels triples (via model managers and known subset of BioModels predicates)


class MetaData(models.Model):
    """ MetaData information.

     From this information the metadata.rdf file for the archive can be generated.
     The information consists of general VCard information and additional RDF.
     """
    description = models.TextField(null=True, blank=True)
    creators = models.ManyToManyField(Creator)
    created = models.DateTimeField(editable=False,null=True, blank=True)
    modified = models.ManyToManyField(Date)
    triples = models.ManyToManyField(Triple)

    objects = MetaDataManager()

    class Meta:
        verbose_name_plural = "meta data"
