"""
This handles the querying of the Ontology lookup service via
their REST API.

see also
https://github.com/matthiaskoenig/tellurium-web/issues/95
https://www.ebi.ac.uk/ols/docs/api
"""
import requests
from urllib.parse import urlencode
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



