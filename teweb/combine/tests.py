from django.test import TestCase


class ArchiveMethodTests(TestCase):

    def test_view_index(self):
        response = self.client.get('/combine/')
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "No archives available.")
        self.assertQuerysetEqual(response.context['archives'], [])
        self.assertTrue('form' in response.context)

    def test_view_about(self):
        response = self.client.get('/combine/about')
        self.assertEqual(200, response.status_code)

    def test_view_archive_404(self):
        response = self.client.get('/combine/12345')
        self.assertTrue(response.status_code in [301, 404])




