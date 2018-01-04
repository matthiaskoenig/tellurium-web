"""
Basic tests.
"""
import os

# setup django environment
from combine.utils import django_setup

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from ..forms import UploadArchiveForm
from .utils import OMEX_SHOWCASE_PATH
from ..utils.data import create_users, add_archives_to_database
from ..fixtures.users import user_defs


BASE_URL = '/'

# environment variables for tests
os.environ["DJANGO_ADMIN_PASSWORD"] = "test"

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
class LoginInViews(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_users(user_defs=user_defs, delete_all=True)

    def setUp(self):

        self.client.login(username="janekg89", password=os.environ['DJANGO_ADMIN_PASSWORD'])

    def test_upload_archive(self):

        path = OMEX_SHOWCASE_PATH

        with open(path, 'rb') as fp:
            file = SimpleUploadedFile("test", fp.read())
            response = self.client.post("/upload",{'file':file })
            self.assertEquals(response.status_code, 302)
            self.assertEquals(response.url, "/archive/1/")










