"""
Testing the metadata and RDF parsing.
"""
from ..metadata import rdf
from .utils import OMEX_SHOWCASE_PATH

# setup django environment
from combine.utils import django_setup

from django.test import TestCase


class RDFTests(TestCase):

    def test_showcase(self):
        metadata = rdf.read_metadata(OMEX_SHOWCASE_PATH)
        assert metadata is not None
