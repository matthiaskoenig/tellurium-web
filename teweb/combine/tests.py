"""
Basic tests.
"""
import os
import sys
import coreapi
import json
import pandas as pd

FILE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
# project directory
PROJECT_DIR = os.path.join(FILE_DIR, "../teweb/")
os.chdir(PROJECT_DIR)
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teweb.settings")
sys.path.append(PROJECT_DIR)
# django setup
import django
django.setup()


from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from django.core.files import File
from django.urls import reverse

from rest_framework.test import APIClient, RequestsClient, APIRequestFactory, APITestCase
from rest_framework import status
from .forms import UploadArchiveForm
from .models import hash_for_file
from . import comex

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OMEX_SHOWCASE_PATH = os.path.join(BASE_DIR, '../../archives/CombineArchiveShowCase.omex')
# This is so my local_settings.py gets loaded.

BASE_URL = '/'


class ArchiveMethodTests(TestCase):

    def test_view_index(self):
        response = self.client.get(BASE_URL)
        self.assertEqual(200, response.status_code)

    def test_view_about(self):
        response = self.client.get(BASE_URL + 'about')
        self.assertEqual(200, response.status_code)

    def test_view_archive_404(self):
        response = self.client.get(BASE_URL + '12345')
        self.assertTrue(response.status_code in [301, 404])

    def test_upload_form_empty(self):
        """ Empty upload form is invalid.

        :return:
        """
        form = UploadArchiveForm(data={})
        self.assertFalse(form.is_valid())

    def test_upload_form_archive(self):
        """ Form with archive is valid
        http://stackoverflow.com/questions/2473392/unit-testing-a-django-form-with-a-filefield

        :return:
        """
        path = OMEX_SHOWCASE_PATH
        upload_file = open(path, 'rb')
        post_dict = {}
        file_dict = {'file': SimpleUploadedFile(upload_file.name, upload_file.read())}
        form = UploadArchiveForm(post_dict, file_dict)
        self.assertTrue(form.is_valid())

    # OMEX Tests
    def test_omex(self):
        # TODO: implement & upload archive & fill database tests for the test database
        pass
        # archive = Archive.objects.get(pk=1)
        # print(archive)
        # get_content(archive)


