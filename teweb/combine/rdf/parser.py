"""
Module for parsing semantic tripples.
Either as RDF (*.rdf) or as Turtle (*.ttl).


RDF is a graph where the nodes are URI references, Blank Nodes or Literals, in RDFLib represented by the classes URIRef, BNode, and Literal.
URIRefs and BNodes can both be thought of as resources, such a person, a company, a web-site, etc.
A BNode is a node where the exact URI is not known. URIRefs are also used to represent the properties/predicates in the RDF graph.
Literals represent attribute values, such as a name, a date, a number, etc.
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
    f1 = "../testdata/rdf/metadata1.rdf"
    f2 = "../testdata/rdf/metadata2.rdf"

    parse_rdf(f2)
