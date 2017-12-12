from __future__ import absolute_import, print_function, unicode_literals
from django.db import models
from django.core.files import File
from django.apps import apps
from django.utils import timezone
from django.contrib.auth.models import User


from combine.models import hash_for_file , Tag
from combine import comex
from six import string_types
import os


class ArchiveManager(models.Manager):

    def get_or_create(self, *args, **kwargs):
        if "archive_path" in kwargs:
            f=kwargs["archive_path"]
            del kwargs["archive_path"]

            kwargs["md5"] = hash_for_file(f, hash_type='MD5')
            new_archive, created = super(ArchiveManager, self).get_or_create(*args, **kwargs)
            if not created:
                return new_archive, created
            else:
                new_archive.name =  name = os.path.basename(f)
                tokens = name.split(".")
                if len(tokens) > 1:
                    name = ".".join(tokens[0:-1])

                new_archive.name = name
                new_archive.file = (name,File(open(f, 'rb')))
                new_archive.created = timezone.now()

                try:
                    if isinstance(kwargs['complex_ligands'], string_types):
                        user = User.objects.get(username=kwargs["user"])
                    else:
                        user = kwargs["user"]
                except:
                    user = User.objects.get(username="global")

                new_archive.user = user
                new_archive.full_clean()
                new_archive.save()
                tags_info = comex.tags_info(f)
                print(tags_info)
                for tag_info in tags_info:
                    tag, created = Tag.objects.get_or_create(name=tag_info.name,
                                                             category=tag_info.category)
                    if created:
                        tag.save()
                    new_archive.tags.add(tag)

            return new_archive, created

        else:
            new_archive, created = super(ArchiveManager, self).get_or_create(*args, **kwargs)
            return new_archive, created




