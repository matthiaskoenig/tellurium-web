"""
Test webservice requests for metadata.
This tests will fail without internet connection.
"""
from django.test import TestCase
from combine.metadata.webservices import json_providers_for_uri, json_term_for_uri

# setup django environment
from combine.utils import django_setup

class RequestOntologyTests(TestCase):

    def test_json_providers_for_uri(self):
        """ Testing retrieval of providers from identifiers.org. """

        test_data_success = [
            "http://identifiers.org/fma/FMA:9670",
            "http://identifiers.org/chebi/CHEBI:4167",
            "http://identifiers.org/go/GO:0005829",
            # alternative but not valid
            "http://identifiers.org/obo.chebi/CHEBI:4167",
            "http://identifiers.org/obo.go/GO:0005829",
        ]

        test_data_empty = [
            "http://identifiers.org/kegg.compound/C00031",  # FIXME: This should work, bug on identifiers.org
            "./tmpx6u6q7ofsmith_chase_nokes_shaw_wake_2004_example_semantics.rdf#entity_1",
        ]
        for uri in test_data_empty:
            json = json_providers_for_uri(uri)
            # pprint(json)
            assert json is not None

            if len(json) > 0:
                assert "message" in json

        for uri in test_data_success:
            json = json_providers_for_uri(uri)
            # pprint(json)
            assert json is not None
            assert len(json) > 0
            for provider in json:
                assert "id" in provider

    def test_json_term_for_uri(self):
        """ Testing retrieval of terms from OLS

        :return:
        """

        test_data_success = [
            "http://identifiers.org/fma/FMA:9670",
            "http://identifiers.org/chebi/CHEBI:4167",
            "http://identifiers.org/go/GO:0005829",
            # alternative but not valid
            "http://identifiers.org/obo.chebi/CHEBI:4167",
            "http://identifiers.org/obo.go/GO:0005829",
        ]

        test_data_empty = [
            "http://identifiers.org/kegg.compound/C00031",
            "./tmpx6u6q7ofsmith_chase_nokes_shaw_wake_2004_example_semantics.rdf#entity_1",
        ]

        for uri in test_data_empty:
            json = json_term_for_uri(uri)
            # pprint(json)
            assert json is not None
            assert len(json) == 0

        for uri in test_data_success:
            json = json_term_for_uri(uri)
            # pprint(json)
            assert json is not None
            assert len(json) > 0
            assert "iri" in json