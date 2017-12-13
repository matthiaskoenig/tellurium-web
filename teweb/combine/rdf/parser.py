"""
Module for parsing semantic tripples.
Either as RDF (*.rdf) or as Turtle (*.ttl).
"""

import rdflib
from rdflib.util import guess_format

from rdflib.namespace import FOAF
from rdflib.namespace import Namespace

# NS = Namespace('http://www.w3.org/2006/vcard/ns#')


def parse_rdf(path):
    g = rdflib.Graph()
    format = guess_format(path)
    print("Format:", format)
    result = g.parse(path, format=format)

    print("graph has %s statements." % len(g))

    for subj, pred, obj in g:
        print((subj, pred, obj))

    s = g.serialize(format='n3')
    # print(str(s))



if __name__ == "__main__":
    f1 = "metadata1.rdf"
    f2 = "metadata2.rdf"

    parse_rdf(f2)
