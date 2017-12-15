"""
Module for parsing semantic tripples.
Either as RDF (*.rdf) or as Turtle (*.ttl).


RDF is a graph where the nodes are URI references, Blank Nodes or Literals, in RDFLib represented by the classes URIRef, BNode, and Literal.
URIRefs and BNodes can both be thought of as resources, such a person, a company, a web-site, etc.
A BNode is a node where the exact URI is not known. URIRefs are also used to represent the properties/predicates in the RDF graph.
Literals represent attribute values, such as a name, a date, a number, etc.
"""

# The serializing to XML
# - drops order of the elements
# - adds internal nodeIds in cases because the following is not set on xml elements:
#       rdf:parseType="Resource" on vCard:n, vCard:org, dcterms:created, dcterms:modified

import rdflib
import os
from rdflib.util import guess_format
from pprint import pprint

from rdflib import Graph  # rdf graph
from rdflib import URIRef, BNode, Literal  # node types

from rdflib.namespace import Namespace
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')
DCTERMS = Namespace('http://purl.org/dc/terms/')
BQMODEL = Namespace('http://biomodels.net/model-qualifiers/')


def bind_default_namespaces(g):
    """ Bind the namespace prefixes in graph

    :param g:
    :return:
    """
    g.bind(prefix="vCard", namespace=URIRef("http://www.w3.org/2006/vcard/ns#"))
    g.bind(prefix="dcterms", namespace=URIRef("http://purl.org/dc/terms/"))
    g.bind(prefix="bqmodel", namespace=URIRef("http://biomodels.net/model-qualifiers/"))


def fix_path_prefix(el, prefix):
    """ Fix prefix via replacement to get relative paths in triples. """
    el_str = str(el)

    # fix relative paths
    if el_str.startswith(prefix):

        # print("replacing prefix:", prefix)
        el_str = el_str.replace(prefix, './')
        if el_str == "./":
            el_str = "."
        # create correct node type
        if isinstance(el, BNode):
            el = BNode(el_str)
        elif isinstance(el, URIRef):
            el = URIRef(el_str)
        elif isinstance(el, Literal):
            el = Literal(el_str)

    return el


def parse_rdf(path):
    """ Parses the rdf in graph. """
    print("-" * 80)
    # file prefix to replace for relative paths
    prefix = "file://{}/".format(os.path.abspath(os.path.dirname(path)))
    print("File prefix:", prefix)

    # parse RDF graph
    g = rdflib.Graph()
    format = guess_format(path)
    print("Format:", format)
    g.parse(path, format=format)
    print("Statements: %s" % len(g))
    print("-" * 80)

    def fix_email(obj):
        """ Fixing wrong parsing of emails. """
        # remove email prefix
        obj_str = str(obj).replace(prefix, '')
        # fix node type
        return Literal(obj_str)

    # new graph with fixed information
    g2 = Graph()
    bind_default_namespaces(g2)

    for subj, pred, obj in g:

        # fixing emails
        if pred == VCARD.hasEmail:
            obj = fix_email(obj)

        # fix prefixes
        subj = fix_path_prefix(subj, prefix)
        pred = fix_path_prefix(pred, prefix)
        obj = fix_path_prefix(obj, prefix)

        # add fixed triples
        g2.add((subj, pred, obj))
        print((subj, pred, obj))


    # Serializing the graph
    if False:
        s2 = g2.serialize(format='pretty-xml')
        print(s2.decode("utf-8"))

        print("\n\n")

        s2 = g2.serialize(format='turtle')
        print(s2.decode("utf-8"))


    return g2


if __name__ == "__main__":
    f1 = "../testdata/rdf/metadata1.rdf"
    f2 = "../testdata/rdf/metadata2.rdf"

    parse_rdf(f2)
    # parse_rdf(f1)
