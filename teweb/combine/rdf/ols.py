"""
This handles the querying of the Ontology lookup service via
their REST API.
https://www.ebi.ac.uk/ols/docs/api

Also handles the MIRIAM registry.
https://www.ebi.ac.uk/miriamws/main/rest/

And the identifiers.org resources.
http://identifiers.org/restws

"""

import warnings
import requests
from pprint import pprint


OLS_BASE_URL = "http://www.ebi.ac.uk/ols/api/"
MIRIAM_BASE_URL = "http://www.ebi.ac.uk/miriamws/main/rest/"
IDENTIFIERS_BASE_URL = "http://identifiers.org/rest/"


def json_providers_for_uri(uri):
    json = {}
    tokens = uri.split("/")
    if len(tokens) < 3:
        pass
    else:
        prefix = tokens[-2]

        # handle invalid, but occuring prefixes
        obo_tokens = prefix.split(".")
        if (len(obo_tokens) == 2) and (obo_tokens[0] == "obo"):
            prefix = obo_tokens[1]

        json = _json_providers_for_prefix(prefix)

    return json


def _json_providers_for_prefix(prefix):
    """ Returns the provider information for given prefix.

    /collections/provider/{prefix} : retrieves a list of provider codes for a matching collection using the prefix (pdb)

    :param prefix
    :return:
    """

    url = IDENTIFIERS_BASE_URL + 'collections/provider/{}'.format(prefix)
    response = requests.get(url)
    return response.json()


def json_term_for_uri(uri):
    """ Performs ols query to retrive JSON for URI.

    :return:
    """
    json = {}

    tokens = uri.split("/")
    query_id = tokens.pop()
    tokens = query_id.split(":")
    if len(tokens) == 1:
        pass
    elif len(tokens) > 2:
        warnings("URI term contains more than 2 parts: {}".format(uri))
    else:
        ontology, iri = tokens
        ontology = ontology.lower()
        iri = "{}_{}".format(ontology.upper(), iri)

        # encode URL
        url = OLS_BASE_URL + 'ontologies/{}/terms/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F{}'.format(ontology, iri)
        response = requests.get(url)
        json = response.json()

    return json


################################################################

def test_json_providers_for_uri():

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
        pprint(json)
        assert json is not None

        if len(json) > 0:
            assert "message" in json

    for uri in test_data_success:
        json = json_providers_for_uri(uri)
        pprint(json)
        assert json is not None
        assert len(json) > 0
        for provider in json:
            assert "id" in provider



def test_json_term_for_uri():
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

################################################################

if __name__ == "__main__":
    test_json_term_for_uri()
    test_json_providers_for_uri()
