"""
Handle the term annotations.
"""
from pprint import pprint

from combine.metadata.webservices import json_providers_for_uri, json_term_for_uri


class Annotation(object):

    def __init__(self, subject, qualifier, uri):
        self.subject = subject
        self.qualifier = qualifier
        self.uri = uri
        self.qualifier = qualifier
        self.parse_uri_info()

    def parse_uri_info(self):
        """ Retrieves JSON.

        :param uri:
        :return:
        """
        json = json_term_for_uri(self.uri)
        pprint(json)
        self.description = json.get("description", None)
        self.label =


    def __str__(self):
        return self.uri

    def html(self):
        qualifier_html = ""




if __name__ == "__main__":
    subject = "./BIOMD0000000176.xml#_525523"
    qualifier = "http://biomodels.net/biology-qualifiers/is"
    uri = "http://identifiers.org/chebi/CHEBI:4167"
    a = Annotation(subject=subject, qualifier=qualifier, uri=uri)
    print(a)
