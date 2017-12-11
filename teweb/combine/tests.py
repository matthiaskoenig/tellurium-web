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
from django.core.urlresolvers import reverse

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


class ViewTestCase(TestCase):
    """Test suite for the api views."""
    def setUp(self):
        """Define the test client and other test variables."""
        self.BASE_URL = "http://127.0.0.1:8001"
        test_archive_dir = os.path.abspath(os.path.join(BASE_DIR, "../../test_archives"))
        self.ARCHIVE_DIRS = [test_archive_dir]
        auth = coreapi.auth.BasicAuthentication(username='mkoenig',
                                                password=os.environ['DJANGO_ADMIN_PASSWORD'])
        self.client = APIClient(auth)
        self.document = self.client.get(BASE_URL + "/api/")
        self.omex_files = comex.get_omex_file_paths(self.ARCHIVE_DIRS)

    def test_get_archives(self):
        for f in self.omex_files:
            name = os.path.basename(f)
            md5 = hash_for_file(f, hash_type='MD5')
            django_file = File(open(f, 'rb'))

    def test_api_can_create_archive(self):
        f = self.omex_files[0]
        name = os.path.basename(f)
        md5 = hash_for_file(f, hash_type='MD5')
        django_file = File(open(f, 'rb'))
        archive_data = {'name': name, 'file': django_file, 'tags': [], 'md5': md5}
        self.ducument["archives"]["create"] = archive_data
        response = self.client.action(self.document["archives", "create"])


        #response = self.client.post(
        #    reverse('create'),
        #    archive_data,
        #    format="json")
        #self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_user(self):
        client = RequestsClient()
        response = client.get('http://testserver/api/users')
        self.assertEquals(response.status_code, 200)


class ViewAPILoggedOut(TestCase):
    """Test suite for the api views."""
    def setUp(self):
        """Define the test client and other test variables."""
        self.client = RequestsClient()

    def test_get_user(self):
        response = self.client.get('http://testserver/api/users')
        self.assertEquals(response.status_code, 403)


class ViewAPILoggedIn(TestCase):
    """Test suite for the api views."""
    def setUp(self):
        self.client.login(username='mkoenig', password=os.environ['DJANGO_ADMIN_PASSWORD'])

    def test_list_users(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('api:user-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'janek89')
        self.assertContains(response, 'mkoenig')

    def test_create_user(self):
        url = reverse('api:user-list')
        post = {"username": "user1", "password": "test1"}
        response = self.client.post(url, post)
        self.assertEquals(response.status_code, 201)
        response = self.client.get(url)
        self.assertContains(response, 'user1')

    def test_detail_user(self):
        url = reverse('api:user-detail', kwargs={'pk': '2'})
        response = self.client.get(url)
        data = response.json()

    def test_delete_user(self):
        url = reverse('api:user-detail', kwargs={'pk': '2'})
        response = self.client.delete(url)
        self.assertEquals(response.status_code, 204)


class ViewAPILoggedOut(TestCase):
    def test_list_users(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('api:user-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'janek89')
        self.assertContains(response, 'mkoenig')
