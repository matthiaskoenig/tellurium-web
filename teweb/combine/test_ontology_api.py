"""
Test request Ontology API.
"""
from combine.rdf import ols
from django.test import TestCase


class RequestOntologyTests(TestCase):

    def test_json_term(self):
        ols.test_json_term_for_uri()

    def test_json_providers(self):
        ols.test_json_providers_for_uri()

