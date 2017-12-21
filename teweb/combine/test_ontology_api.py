"""
Test request Ontology Api.
"""
import os
import sys
from pprint import pprint
import logging


FILE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
# project directory
PROJECT_DIR = os.path.join(FILE_DIR, "../teweb/")
os.chdir(PROJECT_DIR)
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teweb.settings")
sys.path.append(PROJECT_DIR)
# django setup
import django
django.setup()
from django.test import TestCase
from .rdf.ols import get_json_for_term, double_urlencode,single_urlencode
from .models import Triple
from urllib.parse import urlparse, parse_qs,urlunparse
import requests


class RequestOntologyTests(TestCase):

    def test_get_json_for_term(self):
        pprint(get_json_for_term().status_code)

    def test_parse(self):
        bq_triples = [t for t in Triple.objects.all() if t.is_bq()]
        #pprint(bq_triples)



        for triple in bq_triples:
            #print(triple.object)
            object_splitted = triple.object.split("/")
            if 'identifiers.org' in object_splitted:
                id = object_splitted.pop()

                url ="https://www.ebi.ac.uk/miriamws/main/rest/convert?uri="+triple.object

                response = requests.get(url)
                print(response.status_code)
                print(response.json())






                #path = "https://www.ebi.ac.uk/ols/api/ontologies/{}/terms/".format()

        term = double_urlencode("http://purl.obolibrary.org/obo/CHEBI_4167")
        #term=single_urlencode("CHEBI_16236")
        #url=path+term
        #response = requests.get(url)

       # print(response.status_code)
        #pprint(response.json())
        url = "http://identifiers.org/obo.chebi/CHEBI:4167"
        response = requests.get(url)
        print(response.url)
        url = "http://identifiers.org/rest//resources/{id}"
        url = "obo.chebi/CHEBI:4167"







