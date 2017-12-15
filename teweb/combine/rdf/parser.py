"""
Module for parsing semantic tripples.
Either as RDF (*.rdf) or as Turtle (*.ttl).


RDF is a graph where the nodes are URI references, Blank Nodes or Literals, in RDFLib represented by the classes URIRef, BNode, and Literal.
URIRefs and BNodes can both be thought of as resources, such a person, a company, a web-site, etc.
A BNode is a node where the exact URI is not known. URIRefs are also used to represent the properties/predicates in the RDF graph.
Literals represent attribute values, such as a name, a date, a number, etc.
"""

import rdflib
import os
from rdflib.util import guess_format
from pprint import pprint

from rdflib import Graph

# namespaces
from rdflib.namespace import FOAF, DCTERMS
from rdflib.namespace import Namespace

NS = Namespace('http://www.w3.org/2006/vcard/ns#')

# different node types
from rdflib import URIRef, BNode, Literal


def parse_rdf(path):
    """ Parses the rdf in graph"""
    g = rdflib.Graph()
    format = guess_format(path)
    print("Format:", format)

    # get prefix to fix the relative files
    prefix = "file://{}".format(os.path.abspath(os.path.dirname(path)))
    print("PREFIX:", prefix)

    result = g.parse(path, format=format)

    print("graph has %s statements." % len(g))


    def fix_prefix(el):
        el_str = str(el)

        # fix relative paths
        if el_str.startswith(prefix):
            # print("replacing prefix:", prefix)
            el_str = el_str.replace(prefix, '.')
            if el_str == "./":
                el_str = "."
            if isinstance(el, BNode):
                el = BNode(el_str)
            elif isinstance(el, URIRef):
                el = URIRef(el_str)
            elif isinstance(el, Literal):
                el = Literal(el_str)
            print(el)

        return el

    g2 = Graph()

    for subj, pred, obj in g:
        print((subj, pred, obj))

        # TODO: fix the emails

        # Fix the prefixes
        subj = fix_prefix(subj)
        pred = fix_prefix(pred)
        obj = fix_prefix(obj)

        # add triple
        g2.add((subj, pred, obj))
        print((subj, pred, obj))
        print('-' * 80)

        # if subj_str.startswith(prefix):
        #   print("PREFIX found")


        # set values
        # g.set((subj, pred, Literal(43)))
        # if URIRef

            # g.set((bob, FOAF.age, Literal(43)))  # replaces 42 set above
            # print "Bob is now ", g.value(bob, FOAF.age)

        # 'http://www.w3.org/2006/vcard/ns#hasEmail'



    # s = g.serialize(format='n3')
    s = g.serialize(format='pretty-xml')
    # print(s.decode("utf-8"))

    s2 = g2.serialize(format='pretty-xml')
    print(s2.decode("utf-8"))

    return g



if __name__ == "__main__":
    f1 = "../testdata/rdf/metadata1.rdf"
    f2 = "../testdata/rdf/metadata2.rdf"

    parse_rdf(f2)
