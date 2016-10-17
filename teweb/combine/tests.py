from __future__ import print_function, division
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from .models import Archive
from .forms import UploadArchiveForm
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OMEX_SHOWCASE_PATH = os.path.join(BASE_DIR, '../../archives/CombineArchiveShowCase.omex')

BASE_URL = '/combine/'


class ArchiveMethodTests(TestCase):

    def test_view_index(self):
        response = self.client.get(BASE_URL)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "No archives available.")
        self.assertQuerysetEqual(response.context['archives'], [])
        self.assertTrue('form' in response.context)

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


    # def test_upload_view_archive(self):
    #     """ Test archive upload of various files.
    #
    #     :return:
    #     """
    #     # TODO: fix this unit test. Must be possible to test
    #     # The file upload via the view
    #     c = Client()
    #     with open(OMEX_SHOWCASE_PATH) as fp:
    #         response = c.post(BASE_URL, {'file': fp})
    #
    #         archives = Archive.objects.all()
    #         print(len(archives))
    #
    #         # print(response)
    #     self.assertTrue(False)






