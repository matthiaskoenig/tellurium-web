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
from django.core.urlresolvers import reverse
from combine.models import Archive, Tag, hash_for_file
from combine.comex import get_omex_file_paths
from django.contrib.auth.models import User
from collections import namedtuple
from combine import comex


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OMEX_SHOWCASE_PATH = os.path.join(BASE_DIR, '../../archives/CombineArchiveShowCase.omex')
# This is so my local_settings.py gets loaded.
BASE_URL = '/'
UserDef = namedtuple('UserDef', ['username', 'first_name', 'last_name', 'email', 'superuser'])
user_defs = [
    UserDef("janekg89", "Jan", "Grzegorzewski", "janekg89@hotmail.de", True),
    UserDef("mkoenig", "Matthias", "König", "konigmatt@googlemail.com", True),
    UserDef("testuser", False, False, False, False),
    UserDef("global", False, False, False, False)]
ARCHIVE_DIRS = ["../../archives"]


def add_archives_to_database():
    """ Add archives to database.

    :return:
    """
    # list files
    omex_files = comex.get_omex_file_paths(ARCHIVE_DIRS)

    for f in sorted(omex_files):
        print('-' * 80)
        print(f)
        md5 = hash_for_file(f, hash_type='MD5')
        existing_archive = Archive.objects.filter(md5=md5)
        # archive exists already based on the MD5 checksum
        if len(existing_archive) > 0:
            print("Archive already exists, not recreated: {}".format(f))
        else:
            name = os.path.basename(f)
            django_file = File(open(f, 'rb'))
            new_archive = Archive(name=name)
            global_user = User.objects.get(username="global")
            new_archive.user = global_user
            new_archive.file.save(name, django_file, save=False)
            new_archive.md5 = hash_for_file(f, hash_type='MD5')
            new_archive.full_clean()
            new_archive.save()

            # add Tags
            # tag, created = Tag.objects.get_or_create(name="test", type=Tag.TagType.misc)
            # if created:
            #     tag.save()
            # new_archive.tags.add(tag)

            tags_info = comex.tags_info(f)
            print(tags_info)
            for tag_info in tags_info:
                tag, created = Tag.objects.get_or_create(name=tag_info.name,
                                                         category=tag_info.category)
                if created:
                    tag.save()
                new_archive.tags.add(tag)


def create_users(user_defs, delete_all=True):
    """ Create users in database from user definitions.

    :param delete_all: deletes all existing users
    :return:
    """
    if not user_defs:
        user_defs = []

    # deletes all users
    if delete_all:
        User.objects.all().delete()

    # adds user to database
    for user_def in user_defs:
        if user_def.superuser:
            user = User.objects.create_superuser(username=user_def.username, email=user_def.email,
                                                 password= os.environ['DJANGO_ADMIN_PASSWORD'])
        else:
            user = User.objects.create_user(username=user_def.username, email=user_def.email,
                                            password= os.environ['DJANGO_ADMIN_PASSWORD'])
        user.last_name = user_def.last_name
        user.first_name = user_def.first_name
        user.save()

    # display users
    for user in User.objects.all():
        print('\t', user.username, user.email, user.password)


class ViewAPILogedInSuperUser(TestCase):
    """Test suite for the api views."""

    @classmethod
    def setUpTestData(cls):
        create_users(user_defs=user_defs, delete_all=True)
        add_archives_to_database()

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




class ViewAPILogedOut(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_users(user_defs=user_defs, delete_all=True)
        add_archives_to_database()

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

    def test_detail_archives(self):
        """
        Ensure we can create a new account object.
        """
        archive= Archive.objects.get(name="L1V3_ikappab.omex")

        url = reverse('api:archive-detail',kwargs={"uuid": archive.uuid})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'L1V3_ikappab.omex')

class ViewAPILogedIn(TestCase):
    """Test suite for the api views."""

    @classmethod
    def setUpTestData(cls):
        create_users(user_defs=user_defs, delete_all=True)
        add_archives_to_database()

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









