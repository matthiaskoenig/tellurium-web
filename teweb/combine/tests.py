from django.test import TestCase

from django.test import Client


class ArchiveMethodTests(TestCase):

    def test_view_index(self):
        client = Client()
        response = client.get('/combine/')
        self.assertEqual(200, response.status_code)

    def test_view_about(self):
        client = Client()
        response = client.get('/combine/about')
        self.assertEqual(200, response.status_code)




