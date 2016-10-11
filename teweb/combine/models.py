from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.db import models
from django.utils import timezone


@python_2_unicode_compatible
class Archive(models.Model):
    """ Combine Archive class. """
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='archives/%Y/%m/%d')
    created = models.DateTimeField('date published', editable=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ On save, update timestamps. """
        if not self.id:
            self.created = timezone.now()
        return super(Archive, self).save(*args, **kwargs)

