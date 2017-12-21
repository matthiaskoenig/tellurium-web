"""
Test request Ontology API.
"""
from combine.rdf import ols
from django.test import TestCase


class RequestOntologyTests(TestCase):

    def test_parse(self):
        ols.test_parse()
