"""
This handles the querying of the Ontology lookup service via
their REST API.

see also
https://github.com/matthiaskoenig/tellurium-web/issues/95
https://www.ebi.ac.uk/ols/docs/api
"""

import warnings
import requests
from urllib.parse import urlencode
from pprint import pprint







def get_json_for_term():
    """ This uses the objects of biological triples to query OLS
    and get JSON information back.

    e.g., http://identifiers.org/obo.chebi/CHEBI:4167
    GET /ols/api/ontologies/{ontology}/terms/{iri}
    ontology = 'chebi'
    term = 'CHEBI_4167'

    :return:
    """

    response  = requests.get("https://www.ebi.ac.uk/ols/api/ontologies/chebi/terms/"+term)
    return response

def double_urlencode(text):
   """double URL-encode a given 'text'.  Do not return the 'variablename=' portion."""

   text = single_urlencode(text)
   text = single_urlencode(text)

   return text

def single_urlencode(text):
   """single URL-encode a given 'text'.  Do not return the 'variablename=' portion."""

   blah = urlencode({'blahblahblah':text})

   #we know the length of the 'blahblahblah=' is equal to 13.  This lets us avoid any messy string matches
   blah = blah[13:]

   return blah

OLS_BASE_URL = "http://www.ebi.ac.uk/ols/api/"

def json_for_uri(uri):
    """ Performs ols query to retrive JSON for URI.

    :return:
    """
    # print(triple.object)
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


def test_parse():

    test_data_success = [
        "http://identifiers.org/fma/FMA:9670",
        "http://identifiers.org/obo.chebi/CHEBI:4167",
        "http://identifiers.org/obo.go/GO:0005829",
    ]

    test_data_empty = [
        "http://identifiers.org/kegg.compound/C00031",
        "./tmpx6u6q7ofsmith_chase_nokes_shaw_wake_2004_example_semantics.rdf#entity_1",
    ]

    for uri in test_data_empty:
        json = json_for_uri(uri)
        # pprint(json)
        assert json is not None
        assert len(json) == 0

    for uri in test_data_success:
        json = json_for_uri(uri)
        # pprint(json)
        assert json is not None
        assert len(json) > 0
        assert "iri" in json


if __name__ == "__main__":
    test_parse()
