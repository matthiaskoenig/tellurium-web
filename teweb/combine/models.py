"""
Models.
"""

from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.db import models
from django.utils import timezone

# TODO: executed file for download, i.e. archive after execution
# TODO: validation
# TODO: MD5 Hash
# TODO: Filesize {{ value|filesizeformat }}
# TODO: add tags for description

from django.core.validators import ValidationError
# import libcombine
from tellurium import tecombine



def validate_omex(fieldFile):
    """ Validator for the omex file

    :param file:
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


@python_2_unicode_compatible
class Archive(models.Model):
    """ Combine Archive class. """
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='archives/upload', validators=[validate_omex])
    created = models.DateTimeField('date published', editable=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ On save, update timestamps. """
        if not self.id:
            self.created = timezone.now()
        return super(Archive, self).save(*args, **kwargs)

