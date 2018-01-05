"""
Models definitions.
"""
import uuid as uuid_lib
import logging
import os
import io
import datetime
import tempfile
import zipfile

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.contrib.auth.models import User
from djchoices import DjangoChoices, ChoiceItem
from django_model_changes import ChangesMixin
from django.utils.timezone import utc
from django.core.files import File

from celery.result import AsyncResult
from django_celery_results.models import TaskResult


from . import validators, managers
from .metadata.rdf import read_metadata
from .utils import comex
from .metadata import rdf
from .utils.html import input_template, html_creator, html_creator_edit

logger = logging.getLogger(__name__)

# ===============================================================================
# Settings
# ===============================================================================
MAX_TEXT_LENGTH = 500
MANIFEST_LOCATION = "./manifest.xml"
MANIFEST_FORMAT = "http://identifiers.org/combine.specifications/omex-manifest"
METADATA_LOCATION = "./metadata.rdf"
METADATA_FORMAT = "http://identifiers.org/combine.specifications/omex-metadata"
METADATA_LOCATION_TURTLE = "./metadata.ttl"
METADATA_FORMAT_TURTLE = "http://purl.org/NET/mediatypes/text/turtle"


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

    class Meta:
        ordering = ['-date']


class Creator(ChangesMixin, models.Model):
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
                                          value="", size="10")
        last_name_input = input_template(name="creators[][last_name]", placeholder="Family Name", value="",size="10")
        organisation_input = input_template(name="creators[][organisation]", placeholder="Organisation",
                                            value="", size="10")
        email_input = input_template(name="creators[][email]", placeholder="Email", value="", size="10")

        # id_dict = {"class":"Id","value":"delete","id":"delete","type":"button"}
        id_input = input_template(name="creators[][id]", value="new", type="hidden")

        delete_dict = {"class": "btn btn-xs btn-danger", "value": "Delete", "id": "delete", "type": "button"}
        delete_input = input_template(name="creators[][delete]", value="false", type="hidden")
        delete_button = input_template(**delete_dict)

        return "<dl class = 'inline-flex'> <dt>"+delete_button +"</dt>"+html_creator_edit(first_name_input, last_name_input, organisation_input, email_input)\
                +"</dl>"+ id_input + delete_input

    @property
    def html_edit(self):
        """

        :return: HTML representation for rendering of editable triple
        """
        first_name_input = input_template(name="creators[][first_name]", placeholder="First Name", value=self.first_name,size="10")
        last_name_input = input_template(name="creators[][last_name]", placeholder="Family Name", value=self.last_name,size="10")
        organisation_input = input_template(name="creators[][organisation]", placeholder="Organisation", value=self.organisation, size="10")
        email_input = input_template(name="creators[][email]", placeholder="Email", value=self.email, size="10")

        return html_creator_edit(first_name_input, last_name_input, organisation_input, email_input)


class TripleElementType(DjangoChoices):
    """ Categories for the element types. """
    uri = ChoiceItem("<class 'rdflib.term.URIRef'>")
    literal = ChoiceItem("<class 'rdflib.term.Literal'>")
    bnode = ChoiceItem("<class 'rdflib.term.BNode'>")


class Triple(models.Model):
    """ RDF triple store."""
    subject = models.TextField()
    subject_type = models.TextField(choices=TripleElementType.choices)
    predicate = models.TextField()
    predicate_type = models.TextField(choices=TripleElementType.choices)
    object = models.TextField()
    object_type = models.TextField(choices=TripleElementType.choices)

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
    created = models.DateTimeField(editable=False, null=True, blank=True)
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
        """ Returns number of triples
        :return:
        """

        return self.triples.count()

    @property
    def last_modified(self):
        """ Gets the last modified Date.

        :return: date instance or None if no modified dates.
        """
        try:
            return self.modified.filter(date__isnull=False).latest('date')
        except ObjectDoesNotExist:
            return None

    def _add_modified(self):
        """ Adds a modified timestamp to the metadata.

        ! This should never be called directly, but only via
            entry.add_modified()
        """
        date = Date.objects.create(date=timezone.now())
        self.modified.add(date)


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

    def has_sbml(self):
        """ Check if any SBML file in the archive."""
        sedml_entries = self.entries.filter(format__startswith="http://identifiers.org/combine.specifications/sbml")
        return len(sedml_entries) > 0

    def has_cellml(self):
        """ Check if any CellML file in the archive."""
        sedml_entries = self.entries.filter(format__startswith="http://identifiers.org/combine.specifications/cellml")
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

    def reset_task(self):
        """ Resets the task, and removes corresponding task results. """
        if self.task_id:
            task_result = TaskResult.objects.get(task_id=self.task_id)
            task_result.delete()
            self.task_id = ''  # set blank
            self.save()

    def create_omex_bytes(self):
        """Writes current omex zip to io.BytesIO.
        This can than be served as response are stored in file.

        :return:
        """
        # All entries are written including the updated manifest.xml and metadata.rdf
        content = {}
        for entry in self.entries.all():
            location = entry.location
            if location in ["."]:
                continue

            content[location] = entry

        # Open StringIO to grab in-memory ZIP contents
        s = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(s, "w")

        # write all entries
        for location, entry in content.items():
            file_path = entry.path

            # fix paths for writing in zip file
            zip_path = location.replace("./", "")

            # Add file, at correct path, with last_modified time
            modified_date = entry.metadata.last_modified
            if modified_date:
                date_time = modified_date.date
            else:
                # get current date time with server timezone
                date_time = datetime.datetime.utcnow().replace(tzinfo=utc)

            zip_info = zipfile.ZipInfo(filename=zip_path)
            zip_info.date_time = date_time.timetuple()  # set modification date
            zip_info.external_attr = 0o777 << 16  # give full access to included file

            with open(file_path, "rb") as f:
                zf.writestr(zip_info, f.read())

                # zf.write(fpath, zip_path)

        # Must close zip for all contents to be written
        zf.close()
        return s

    def update_manifest_entry(self):
        """ Updates the manifest entry of this archive based on the latest information.
        This function must be called if any content of the archive entries change, i.e,
        - adding entries
        - removing entries
        - changing formats

        ! This functions only should be called if something changed in any of the entries.
          This adds new modified timestamps without checking for changes !

        :return: None
        """
        manifest_entry = self.entries.filter(location=MANIFEST_LOCATION).first()
        if manifest_entry:
            # update modified timestamp
            manifest_entry.add_modified()
        else:
            # create new entry
            manifest_entry = ArchiveEntry.objects.create(archive=self,
                                                         source=EntrySource.zip,
                                                         master=False,
                                                         location=MANIFEST_LOCATION,
                                                         format=MANIFEST_FORMAT)
            manifest_entry.set_new_metadata(description="Manifest file describing COMBINE archive content", save=True)

        # create latest manifest.xml
        manifest = comex.create_manifest(archive=self)
        suffix = MANIFEST_LOCATION.split('/')[-1]
        tmp = tempfile.NamedTemporaryFile("w", suffix=suffix)
        tmp.write(manifest)
        tmp.seek(0)  # rewind file for reading !

        # add/update file to manifest entry
        name = MANIFEST_LOCATION.replace("./", "")
        with open(tmp.name, 'rb') as f:
            manifest_entry.file.save(name, File(f))
        tmp.close()

        manifest_entry.save()
        self.save()

    def update_metadata_entry(self):
        """ Updates the metadata files in the archive.

        Must be called after changes to the metadata.
        """
        # ------------------
        # XML serialization
        # ------------------
        metadata_entry = self.entries.filter(location=METADATA_LOCATION).first()
        if metadata_entry:
            # update modified timestamp
            metadata_entry.add_modified()
        else:
            # create new entry
            metadata_entry = ArchiveEntry.objects.create(archive=self,
                                                         source=EntrySource.zip,
                                                         master=False,
                                                         location=METADATA_LOCATION,
                                                         format=METADATA_FORMAT)
            metadata_entry.set_new_metadata(description="Metadata file describing COMBINE archive content as XML serialization.", save=True)
            self.update_manifest_entry()

        # create metadata
        metadata = rdf.create_metadata(archive=self, rdf_format="pretty-xml")
        tmp = tempfile.NamedTemporaryFile("w")
        tmp.write(metadata)
        tmp.seek(0)  # rewind file for reading !

        # add/update file to manifest entry
        name = METADATA_LOCATION.replace("./", "")
        with open(tmp.name, 'rb') as f:
            metadata_entry.file.save(name, File(f))
        tmp.close()

        metadata_entry.save()
        self.save()

        # -----------------------
        # TURTLE serialization
        # -----------------------
        turtle_entry = self.entries.filter(location=METADATA_LOCATION_TURTLE).first()
        if turtle_entry:
            turtle_entry.add_modified()
        else:
            # create new entry
            turtle_entry = ArchiveEntry.objects.create(archive=self,
                                                         source=EntrySource.zip,
                                                         master=False,
                                                         location=METADATA_LOCATION_TURTLE,
                                                         format=METADATA_FORMAT_TURTLE)
            turtle_entry.set_new_metadata(description="Metadata file describing COMBINE archive content as Turtle serialization.", save=True)
            self.update_manifest_entry()

        # create metadata
        metadata = rdf.create_metadata(archive=self, rdf_format="turtle")

        tmp = tempfile.NamedTemporaryFile("w")
        tmp.write(metadata)
        tmp.seek(0)  # rewind file for reading !

        # add/update file to manifest entry
        name = METADATA_LOCATION_TURTLE.replace("./", "")
        with open(tmp.name, 'rb') as f:
            turtle_entry.file.save(name, File(f))
        tmp.close()

        turtle_entry.save()
        self.save()




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

    def __unicode__(self):
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

    def add_modified(self):
        self.metadata._add_modified()

    def set_new_metadata(self, description=None, save=True):
        """ Sets new minimal metadata on entry.

        Used for all entries which do not have metadata associated.
        """
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        meta_dict = {
            'about': self.location,
            'description': description,
            'created': now,
            'modified': (now,),
            'creators': [],
            'bm_triples': [],
            'triples': [],
        }
        metadata_dict = {
            "metadata": meta_dict,
        }
        metadata = MetaData.objects.create(**metadata_dict)

        # FIXME: update triples

        self.metadata = metadata
        if save:
            self.save()


############################
# Channels
############################
# Testing channels

class Job(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    completed = models.DateTimeField(null=True, blank=True)
    celery_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ('created',)

    def __unicode__(self):
        return self.name
