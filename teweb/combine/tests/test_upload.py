"""
Upload Archive tests.
"""
import os
# setup django environment
from combine.utils import django_setup

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .utils import OMEX_SHOWCASE_PATH
from ..utils.data import create_users, add_archives_to_database
from ..fixtures.users import user_defs

BASE_URL = '/'

# environment variables for tests
os.environ["DJANGO_ADMIN_PASSWORD"] = "test"

class UploadinView(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_users(user_defs=user_defs, delete_all=True)

    def setUp(self):

        self.client.login(username="janekg89", password=os.environ['DJANGO_ADMIN_PASSWORD'])

    def test_upload_archive_via_file(self):

        with open(OMEX_SHOWCASE_PATH, 'rb') as fp:
            file = SimpleUploadedFile("test", fp.read())
            response = self.client.post("/upload",{'file':file })
            self.assertEquals(response.status_code, 302)
            self.assertEquals(response.url, "/archive/1/")

    def test_upload_archive_via_url(self):
        archive_url = "https://wwwdev.ebi.ac.uk/biomodels/model/download/BIOMD0000000012"
        response = self.client.post("/upload", {'url': archive_url})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, "/archive/1/")

    #def test_upload_archive_via_url(self):
    #    archive_url = "https://jjj.bio.vu.nl//models/eperiments/adlung2017_fig2g/export/combinearchive?download=1"
    #    response = self.client.post("/upload", {'url': archive_url})
    #    self.assertEquals(response.status_code, 302)
    #    self.assertEquals(response.url, "/archive/1/")

