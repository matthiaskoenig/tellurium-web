"""
Web service queries for metadata.

This handles for instance querying the Ontology Lookup Service (OLS) via their REST API
https://www.ebi.ac.uk/ols/docs/api
to retrieve the information about annotation terms.

Also handles the MIRIAM registry
https://www.ebi.ac.uk/miriamws/main/rest/

And the identifiers.org resources
http://identifiers.org/restws
"""

import warnings
from pprint import pprint

import requests

# caching of webservice requests
import requests_cache
requests_cache.install_cache(backend="redis", cache_name="annotations", expire_after=86400)

# expired only removed on next access, so make sure the cache is cleared
requests_cache.remove_expired_responses()


# from functools import lru_cache
# @lru_cache(maxsize=500)

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




if __name__ == "__main__":
    uri = "http://identifiers.org/chebi/CHEBI:4167"
    json_term = json_term_for_uri(uri)
    pprint(json_term)
    json_providers = json_providers_for_uri(uri)
    pprint(json_providers)

