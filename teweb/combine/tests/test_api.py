"""
Testing the API.
"""

import os

# setup of django
from ..utils import django_setup

from django.test import TestCase
from django.urls import reverse
from django.core.files import File

from ..models import Archive
from ..managers import hash_for_file
from ..utils.comex import get_archive_paths
from ..utils.data import create_users, add_archives_to_database

# testdata
from .utils import ARCHIVE_DIRS
from ..fixtures.users import user_defs

# environment variables for tests
os.environ["DJANGO_ADMIN_PASSWORD"] = "test"

# base url for tests
BASE_URL = '/'


class ViewAPILoggedInSuperUser(TestCase):
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
        archive= Archive.objects.get(name="L1V3_ikappab")

        url = reverse('api:archive-detail', kwargs={"uuid": archive.uuid})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'L1V3_ikappab')

        url_archive = reverse('combine:archive', kwargs={'archive_id': archive.id})
        url_tree = url_archive + "zip_tree"

        # permission for zip tree for global archive
        response_tree = self.client.get(url_tree)
        self.assertEquals(response_tree.status_code, 200)

    def test_delete_user(self):
        url = reverse('api:user-detail', kwargs={'pk': '2'})
        response = self.client.delete(url)
        self.assertEquals(response.status_code, 204)

    def test_create_archive(self):
        url = reverse('api:archive-list')
        omex_files = get_archive_paths(ARCHIVE_DIRS)
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
        archive = Archive.objects.get(name="L1V3_ikappab")

        url = reverse('api:archive-detail',kwargs={"uuid": archive.uuid})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'L1V3_ikappab')


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
        archive= Archive.objects.get(name="L1V3_ikappab")

        url = reverse('api:archive-detail', kwargs={"uuid": archive.uuid})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'L1V3_ikappab')

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
        omex_files = get_archive_paths(ARCHIVE_DIRS)
        f = omex_files[0]
        name = os.path.basename(f)
        md5 = hash_for_file(f, hash_type='MD5')
        django_file = File(open(f, 'rb'))
        archive_data = {'name': name+"test", 'file': django_file, 'tags': [], 'md5': md5}
        response = self.client.post(url, archive_data)
        self.assertEquals(response.status_code, 201)

        # get zip tree url of testuser and global archive
        archive_testuser = Archive.objects.get(user__username="testuser")
        archive_global = Archive.objects.filter(user__username="global").first()

        url_archive_testuser = reverse('combine:archive', kwargs={'archive_id':archive_testuser.id})
        url_tree_testuser = url_archive_testuser + "zip_tree"

        url_archive_global = reverse('combine:archive', kwargs={'archive_id': archive_global.id})
        url_tree_global = url_archive_global + "zip_tree"

        # check if zip tree is accessable for the user who created
        response_tree = self.client.get(url_tree_testuser)
        self.assertEquals(response_tree.status_code, 200)
        #check if global archive zip accessable for user
        response_tree = self.client.get(url_tree_global)
        self.assertEquals(response_tree.status_code, 200)

        response = self.client.get(url)
        self.assertContains(response, name+"test")
        for archive in response.json():
            if archive["name"] == name+"test":
                new_archive = archive

        # should not be seen after logout testuser zip tree
        self.client.logout()
        response = self.client.get(url)
        self.assertNotContains(response, name+"test")

        #no permission for zip tree for logout of testuser
        response_tree = self.client.get(url_tree_testuser)
        self.assertEquals(response_tree.status_code, 403)

        #still permission for zip tree for global archive
        response_tree = self.client.get(url_tree_global)
        self.assertEquals(response_tree.status_code, 200)

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
