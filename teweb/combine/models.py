from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.db import models


@python_2_unicode_compatible
class Archive(models.Model):
    """ Combine Archive class. """
    name = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published', auto_created=True)
    file = models.FileField(upload_to='archives/%Y/%m/%d')

    def __str__(self):
        return self.name

