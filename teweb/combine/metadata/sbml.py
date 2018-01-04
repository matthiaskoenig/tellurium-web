"""
Module for working with SBML annotations.
"""
import os
from pprint import pprint
import logging

import rdflib
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib.util import guess_format
from rdflib.namespace import Namespace, RDF

from combine.metadata.rdf import bind_default_namespaces


try:
    import libsbml
except:
    import tesbml as libsbml

logger = logging.getLogger(__name__)

# TODO: promote SBO terms
# TODO: read annotations


def promote_sbo_terms(doc: libsbml.SBMLDocument) -> libsbml.SBMLDocument:
    """
    Add the SBOTerms to the RDF.
    Autogenerates metaids if necessary.

    :param doc:
    :return: SBMLDocument with SBOTerms in annotations.
    """
    elements = doc.getListOfAllElements()

    for element in doc.getListOfAllElements():

        element = element  # type: libsbml.SBase

        # libsbml
        if element.isSetSBOTerm():
            sbo = print('SBO:', element.getSBOTermID())




def parse_annotations(doc: libsbml.SBMLDocument) -> rdflib.Graph:
    """ Parses the annotations from a given SBML file.

    Return RDF graph of triples.

    :param doc:
    :return:
    """
    g = rdflib.Graph()
    bind_default_namespaces(g)

    # iterate over all SBases
    for element in doc.getListOfAllElements():

        element = element  # type: libsbml.SBase

        # libsbml
        if element.isSetSBOTerm():
            sbo = print('SBO:', element.getSBOTermID())

        annotation = element.getAnnotation()  # type: libsbml.XMLNode
        if annotation:
            print()
            print(element)
            rdf_node = annotation.getChild("RDF")  # type: libsbml.XMLNode
            rdf_node.toString()
            rdf_str = rdf_node.toXMLString()  # type: str
            print(rdf_str)

            # parse RDF
            g_element = rdflib.Graph()
            g_element.parse(data=rdf_str, format="xml")

            # add triples to graph
            for triple in g_element:
                g.add(triple)

    ttl = g.serialize(format='turtle').decode("utf-8")
    print("-" * 80)
    print(ttl)
    print("-" * 80)

    return g


if __name__ == "__main__":
    print("PARSE ANNOTATIONS SBML")
    path = "./BIOMD0000000176.xml"
    assert os.path.exists(path)

    doc = libsbml.readSBMLFromFile(path)  # libsbml.SBMLDocument
    g = parse_annotations(doc)

