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

from combine.models import hash_for_file, Archive
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files import File


from rest_framework.test import APIClient, RequestsClient, APIRequestFactory, APITestCase
from rest_framework import status
from django.urls import reverse
from combine.models import Archive, Tag, hash_for_file
from combine.comex import get_omex_file_paths
from django.contrib.auth.models import User
from collections import namedtuple
from combine import comex


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OMEX_SHOWCASE_PATH = os.path.join(BASE_DIR, '../../archives/CombineArchiveShowCase.omex')
# This is so my local_settings.py gets loaded.
BASE_URL = '/'

from combine.data import UserDef, create_users, add_archives_to_database

user_defs = [
    UserDef("janekg89", "Jan", "Grzegorzewski", "janekg89@hotmail.de", True),
    UserDef("mkoenig", "Matthias", "König", "konigmatt@googlemail.com", True),
    UserDef("testuser", False, False, False, False),
    UserDef("global", False, False, False, False)]
ARCHIVE_DIRS = ["../../archives"]


class ViewAPILogedInSuperUser(TestCase):
    """Test suite for the api views."""

    @classmethod
    def setUpTestData(cls):
        create_users(user_defs=user_defs, delete_all=True)
        add_archives_to_database(ARCHIVE_DIRS)

    def setUp(self):
        self.client.login(username='mkoenig', password=os.environ['DJANGO_ADMIN_PASSWORD'])

    def test_list_users(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('api:user-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'janekg89')
        self.assertContains(response, 'mkoenig')

    def test_create_user(self):
        url = reverse('api:user-list')
        post = {"username":"user1","password":"test1"}
        response = self.client.post(url,post)
        self.assertEquals(response.status_code, 201)
        response = self.client.get(url)
        self.assertContains(response, 'user1')

    def test_detail_user(self):
        url = reverse('api:user-detail', kwargs={'pk':'2'})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_detail_archives(self):
        """
        Ensure we can create a new account object.
        """
        archive= Archive.objects.get(name="L1V3_ikappab.omex")

        url = reverse('api:archive-detail',kwargs={"uuid": archive.uuid})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'L1V3_ikappab.omex')

    def test_delete_user(self):
        url = reverse('api:user-detail', kwargs={'pk': '2'})
        response = self.client.delete(url)
        self.assertEquals(response.status_code, 204)

    def test_create_archive(self):
        url = reverse('api:archive-list')
        omex_files = get_omex_file_paths(ARCHIVE_DIRS)
        f = omex_files[0]
        name = os.path.basename(f)
        md5 = hash_for_file(f, hash_type='MD5')
        django_file = File(open(f, 'rb'))
        archive_data = {'name': name+"test", 'file': django_file, 'tags': [], 'md5': md5}
        response = self.client.post(url, archive_data)
        self.assertEquals(response.status_code, 201)
        response = self.client.get(url)
        self.assertContains(response, name+"test")
        # should not be seen after logout
        self.client.logout()
        response = self.client.get(url)
        self.assertNotContains(response, name+"test")

    def test_list_tags(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('api:tag-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'sbml')

    def test_create_tags_bad_request(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('api:tag-list')
        post = {"category": "user1", "name": "test1"}
        response = self.client.post(url, post)
        self.assertEquals(response.status_code, 400)

    def test_create_tags(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('api:tag-list')
        post = {"category": "format", "name": "test1"}
        response = self.client.post(url, post)
        self.assertEquals(response.status_code, 201)
        response = self.client.get(url)
        self.assertContains(response, 'test1')


class ViewAPILoggedOut(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_users(user_defs=user_defs, delete_all=True)
        add_archives_to_database(ARCHIVE_DIRS)

    def test_list_archives(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('api:archive-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'repressilator')

    def test_list_tags(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('api:tag-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'sbml')

    def test_list_users(self):
        """
        """
        url = reverse('api:user-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 403)

    def test_create_user(self):
        url = reverse('api:user-list')
        post = {"username": "user1", "password": "test1"}
        response = self.client.post(url, post)
        self.assertEquals(response.status_code, 403)

    def test_detail_user(self):
        url = reverse('api:user-detail', kwargs={'pk':'2'})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 403)

    def test_delete_user(self):
        url = reverse('api:user-detail', kwargs={'pk': '2'})
        response = self.client.delete(url)
        self.assertEquals(response.status_code, 403)

    def test_detail_archives(self):
        """
        Ensure we can create a new account object.
        """
        archive= Archive.objects.get(name="L1V3_ikappab.omex")

        url = reverse('api:archive-detail',kwargs={"uuid": archive.uuid})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'L1V3_ikappab.omex')


class ViewAPILoggedIn(TestCase):
    """Test suite for the api views."""

    @classmethod
    def setUpTestData(cls):
        create_users(user_defs=user_defs, delete_all=True)
        add_archives_to_database(ARCHIVE_DIRS)

    def setUp(self):
        self.client.login(username='testuser', password=os.environ['DJANGO_ADMIN_PASSWORD'])

    def test_list_archives(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('api:archive-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'repressilator')

    def test_detail_archives(self):
        """
        Ensure we can create a new account object.
        """
        archive= Archive.objects.get(name="L1V3_ikappab.omex")

        url = reverse('api:archive-detail',kwargs={"uuid": archive.uuid})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'L1V3_ikappab.omex')

    def test_list_tags(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('api:tag-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'sbml')

    def test_list_users(self):
        """
        """
        url = reverse('api:user-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 403)

    def test_create_user(self):
        url = reverse('api:user-list')
        post = {"username":"user1","password":"test1"}
        response = self.client.post(url,post)
        self.assertEquals(response.status_code, 403)

    def test_detail_user(self):
        url = reverse('api:user-detail', kwargs={'pk':'2'})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 403)

    def test_delete_user(self):
        url = reverse('api:user-detail', kwargs={'pk': '2'})
        response = self.client.delete(url)
        self.assertEquals(response.status_code, 403)

    def test_create_archive(self):
        url = reverse('api:archive-list')
        ARCHIVE_DIRS = ["../../archives"]
        omex_files = get_omex_file_paths(ARCHIVE_DIRS)
        f = omex_files[0]
        name = os.path.basename(f)
        md5 = hash_for_file(f, hash_type='MD5')
        django_file = File(open(f, 'rb'))
        archive_data = {'name': name+"test", 'file': django_file, 'tags': [], 'md5': md5}
        response = self.client.post(url, archive_data)
        self.assertEquals(response.status_code, 201)
        response = self.client.get(url)
        self.assertContains(response, name+"test")
        for archive in response.json():
            if archive["name"]== name+"test":
                new_archive = archive

        # should not be seen after logout
        self.client.logout()
        response = self.client.get(url)
        self.assertNotContains(response, name+"test")

        #no permission
        self.client.login(username='global', password=os.environ['DJANGO_ADMIN_PASSWORD'])
        url_detail = reverse('api:archive-detail', kwargs={"uuid": new_archive["uuid"]})
        response = self.client.delete(url_detail)
        self.assertEquals(response.status_code, 403)

        #permission
        self.client.logout()
        self.client.login(username='testuser', password=os.environ['DJANGO_ADMIN_PASSWORD'])
        response = self.client.delete(url_detail)
        self.assertEquals(response.status_code, 204)