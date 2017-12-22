"""
Test webservice requests for metadata.
This tests will fail without internet connection.
"""
from django.test import TestCase
from combine.metadata import webservices

# setup django environment
from combine.utils import django_setup

class RequestOntologyTests(TestCase):

    def test_json_term(self):
        webservices.test_json_term_for_uri()

    def test_json_providers(self):
        webservices.test_json_providers_for_uri()

