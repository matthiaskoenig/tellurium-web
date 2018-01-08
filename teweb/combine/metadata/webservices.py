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
import logging

# caching of webservice requests
import requests_cache
# requests_cache.install_cache(backend="redis", cache_name="annotations", expire_after=86400)
# CACHE_SESSION = requests_cache.CachedSession(backend="redis", cache_name="annotations", expire_after=86400)

# requests_cache.install_cache(backend="re", cache_name="annotations", expire_after=86400)

# expired only removed on next access, so make sure the cache is cleared
# requests_cache.remove_expired_responses()
from functools import lru_cache
# @lru_cache(maxsize=500)

OLS_BASE_URL = "http://www.ebi.ac.uk/ols/api/"
MIRIAM_BASE_URL = "http://www.ebi.ac.uk/miriamws/main/rest/"
IDENTIFIERS_BASE_URL = "http://identifiers.org/rest/"

logger = logging.getLogger(__name__)

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
    response = _make_request(url)
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
        OLS_PATTERN = 'ontologies/{}/terms/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F{}'
        url = OLS_BASE_URL + OLS_PATTERN.format(ontology, iri)
        response = _make_request(url)
        json = response.json()

    return json


@lru_cache(maxsize=2000)
def _make_request(url):
    """ Performs request, returns response.

    :param url:
    :return:
    """
    # response = requests.get(url)
    logging.info("web service request: {}".format(url))
    # response = CACHE_SESSION.get(url)
    # logger.warning("cached {}: ".format(url, response.is_cached))
    response = requests.get(url)
    print("request:", url)

    return response


if __name__ == "__main__":
    uri = "http://identifiers.org/chebi/CHEBI:4167"
    json_term = json_term_for_uri(uri)
    pprint(json_term)
    json_providers = json_providers_for_uri(uri)
    pprint(json_providers)

