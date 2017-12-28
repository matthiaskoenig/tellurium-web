"""
Models definitions.
"""
import uuid as uuid_lib
import logging
import os

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.contrib.auth.models import User
from djchoices import DjangoChoices, ChoiceItem
from django_model_changes import ChangesMixin
from celery.result import AsyncResult

from . import validators, managers
from .metadata.rdf import read_metadata
from .utils import comex
from .utils.html import input_template, html_creator

logger = logging.getLogger(__name__)

# ===============================================================================
# Settings
# ===============================================================================
MAX_TEXT_LENGTH = 500


# ===============================================================================
# MetaData
# ===============================================================================
class Date(models.Model):
    """ Helper class for dates.
    Used to manage the created and modified dates.
    """
    date = models.DateTimeField()

    def __str__(self):
        return str(self.date)


class Creator(ChangesMixin,models.Model):
    """ RDF creator of archive entry. """
    first_name = models.CharField(max_length=MAX_TEXT_LENGTH, blank=True, null=True)
    last_name = models.CharField(max_length=MAX_TEXT_LENGTH, blank=True, null=True)
    organisation = models.CharField(max_length=MAX_TEXT_LENGTH, blank=True, null=True)
    email = models.EmailField(max_length=MAX_TEXT_LENGTH, blank=True, null=True)

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)

    @property
    def html(self):
        """ HTML representation.

        :return: html string
        """
        return html_creator(self.first_name, self.last_name, self.organisation, self.email)

    @staticmethod
    def html_empty():
        """ HTML representation empty.

        :return: html string
        """
        first_name_input = input_template(name="creators[][first_name]", placeholder="First Name",
                                          value="")
        last_name_input = input_template(name="creators[][last_name]", placeholder="Family Name", value="")
        organisation_input = input_template(name="creators[][organisation]", placeholder="Organisation",
                                            value="")
        email_input = input_template(name="creators[][email]", placeholder="Email", value="")

        # id_dict = {"class":"Id","value":"delete","id":"delete","type":"button"}
        id_input = input_template(name="creators[][id]", value="new", type="hidden")

        delete_dict = {"class": "btn btn-default btn-space", "value": "delete", "id": "delete", "type": "button"}
        delete_input = input_template(name="creators[][delete]", value="false", type="hidden")
        delete_button = input_template(**delete_dict)

        return delete_button + html_creator(first_name_input, last_name_input, organisation_input, email_input)\
                + id_input + delete_input

    @property
    def html_edit(self):
        """

        :return: HTML representation for rendering of editable triple
        """
        first_name_input = input_template(name="creators[][first_name]", placeholder="First Name", value=self.first_name)
        last_name_input = input_template(name="creators[][last_name]", placeholder="Family Name", value=self.last_name)
        organisation_input = input_template(name="creators[][organisation]", placeholder="Organisation", value=self.organisation)
        email_input = input_template(name="creators[][email]", placeholder="Email", value=self.email)

        return html_creator(first_name_input, last_name_input, organisation_input, email_input)


class Triple(models.Model):
    """ RDF triple store."""
    subject = models.TextField()
    predicate = models.TextField()
    object = models.TextField()

    def __str__(self):
        return "({}, {}, {})".format(self.subject, self.predicate, self.object)


    @property
    def html(self):
        """

        :return: HTML representation for rendering of triple
        """
        from .metadata import annotation
        a = annotation.Annotation(subject=self.subject, qualifier=self.predicate, uri=self.object)
        return a.html()


    def is_bq(self):
        """ Triple with biomodels qualifer predictate.

        Returns if this is biological relevant triple.
        """
        return self.predicate.startswith("http://biomodels.net/")


class MetaData(ChangesMixin,models.Model):
    """ MetaData information.

    Stores the RDF MetaData for a given object.
    This consists of general information like descriptions, creators, created and modified dates
    and additional set of triples for the object.

    The information consists of general VCard information and additional RDF.
     """
    description = models.TextField(null=True, blank=True)
    creators = models.ManyToManyField(Creator)
    created = models.DateTimeField(editable=False,null=True, blank=True)
    modified = models.ManyToManyField(Date)
    triples = models.ManyToManyField(Triple)

    objects = managers.MetaDataManager()

    def get_triples(self):
        """ This get the subset of annotation triples which are displayed.

        :return:
        """
        # triples = self.triples.filter(subject__startswith=self.entry.location)
        bq_triples = [t for t in self.triples.all() if t.is_bq()]
        return bq_triples

    class Meta:
        verbose_name_plural = "meta data"

    @property
    def triple_count(self):
        return self.triples.count()

# ===============================================================================
# COMBINE Archives
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
    created = models.DateTimeField('date published', editable=False, auto_now=True)
    md5 = models.CharField(max_length=36, blank=True)
    task_id = models.CharField(max_length=100, blank=True)
    tags = models.ManyToManyField(Tag, related_name="archives")
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    uuid = models.UUIDField(  # Used by the API to look up the record
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)

    objects = managers.ArchiveManager()

    def __str__(self):
        return "{}".format(self.name)

    def save(self, *args, **kwargs):
        """ On save, update timestamps. """
        if not self.id:
            self.created = timezone.now()

        if not self.md5:
            self.md5 = managers.hash_for_file(self.file, hash_type='MD5')

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

    @property
    def metadata(self):
        """ Get metadata from the metadata of top level entry."""
        metadata = ""
        try:
            entry = self.entries.get(location=".")
            metadata = entry.metadata
        except ObjectDoesNotExist:
            pass
        return metadata

    def has_sedml(self):
        """ Check if any SED-ML file in the archive."""
        sedml_entries = self.entries.filter(format__startswith="http://identifiers.org/combine.specifications/sed-ml")
        return len(sedml_entries) > 0




    def has_entries(self):
        """ Check if ArchiveEntries exist for archive. """
        return self.entries.count() > 0

    def omex_entries(self):
        """ Get entry information from manifest.

        :return: dictionary {location: entry} for all entries in the manifest.xml
        """
        return comex.EntryParser.read_manifest_entries(self.path)

    def omex_metadata(self):
        """ Get metadata information from archive.

        :return: dictionary {location: metadata}
        """
        return read_metadata(self.path)

    def tree_json(self):
        """ Gets the zip tree as JSON for the archive.

        The entry information is added to the tree.
        """
        entries = self.entries.all()
        return comex.zip_tree_content(self.path, entries)


class EntrySource(DjangoChoices):
    """ Source of the entry information. """
    manifest = ChoiceItem("manifest")
    zip = ChoiceItem("zip")


def get_entry_upload_path(instance, filename):
    """ Path for upload of file for ArchiveEntry.

    :param instance:
    :param filename:
    :return:
    """
    return os.path.join("entries", instance.archive.name, filename)


class ArchiveEntry(ChangesMixin, models.Model):

    """ Entry information.
    This corresponds to the content of the manifest file.
    """
    archive = models.ForeignKey(Archive, on_delete=models.CASCADE, related_name="entries")
    file = models.FileField(upload_to=get_entry_upload_path, null=True)
    location = models.CharField(max_length=MAX_TEXT_LENGTH)
    format = models.CharField(max_length=MAX_TEXT_LENGTH)
    source = models.CharField(max_length=MAX_TEXT_LENGTH, choices=EntrySource.choices)
    master = models.BooleanField(default=False)
    metadata = models.OneToOneField("MetaData", on_delete=models.SET_NULL, null=True, related_name="entry")

    objects = managers.ArchiveEntryManager()

    def __str__(self):
        return "{}:{}".format(self.archive, self.location)

    class Meta:
        verbose_name_plural = "archive entries"

    @property
    def name(self):
        return os.path.splitext(self.location)[0]

    @property
    def short_format(self):
        return comex.short_format(self.format)

    @property
    def base_format(self):
        return comex.base_format(self.format)

    @property
    def path(self):
        return str(self.file.path)







