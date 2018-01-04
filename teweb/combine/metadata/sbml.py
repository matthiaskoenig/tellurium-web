"""
Module for working with SBML annotations.
"""
import os
from pprint import pprint
import logging

import rdflib
import uuid
from combine.metadata.rdf import bind_default_namespaces


try:
    import libsbml
except:
    import tesbml as libsbml

logger = logging.getLogger(__name__)

# TODO: promote SBO terms


def promote_sbo_to_rdf(doc: libsbml.SBMLDocument) -> libsbml.SBMLDocument:
    """
    Add the SBOTerms to the RDF.
    Autogenerates metaids if necessary.

    :param doc:
    :return: SBMLDocument with SBOTerms in annotations.
    """

    for element in doc.getListOfAllElements():

        element = element  # type: libsbml.SBase

        if element.isSetSBOTerm():
            sbo = element.getSBOTermID()
            # check cv terms

            contains_sbo = False

            for k_cv in range(element.getNumCVTerms()):  # type: libsbml.CVTerm
                if contains_sbo:
                    break

                cvterm = element.getCVTerm(k_cv)

                qualifier_type = cvterm.getQualifierType()
                if qualifier_type == libsbml.BIOLOGICAL_QUALIFIER:
                    bqual_type = cvterm.getBiologicalQualifierType()
                    qualifier = libsbml.BiolQualifierType_toString(bqual_type)
                elif qualifier_type == libsbml.MODEL_QUALIFIER:
                    mqual_type = cvterm.getModelQualifierType()
                    qualifier = libsbml.ModelQualifierType_toString(mqual_type)
                elif qualifier_type == libsbml.UNKNOWN_QUALIFIER:
                    qualifier = "unknown"

                if qualifier is None:
                    logger.error("Qualifier could not be parsed!")

                for k_res in range(cvterm.getNumResources()):
                    uri = cvterm.getResourceURI(k_res)
                    print(qualifier, uri)
                    if uri.endswith(sbo):
                        contains_sbo = True
                        break

            # add the cvterm
            if not contains_sbo:
                # set meta id
                if not element.isSetMetaId():
                    # FIXME: this is not reproducible
                    metaid = uuid.uuid4()
                    element.setMetaId(metaid)

                # add cvterm
                uri = "http://identifiers.org/sbo/" + sbo
                cvterm = libsbml.CVTerm()
                cvterm.setModelQualifierType(libsbml.BQM_IS)
                cvterm.addResource(uri)
                code = element.addCVTerm(cvterm)

                if code is not libsbml.LIBSBML_OPERATION_SUCCESS:
                    logger.error("Setting SBO CVTerm '{}' on {} failed with {}".format(sbo, element, code))
                    logger.error(libsbml.OperationReturnValue_toString(code))


    return doc




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
            # print(rdf_str)

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
    print(libsbml.getLibSBMLDottedVersion())
    path = "./BIOMD0000000012.xml"
    assert os.path.exists(path)

    doc = libsbml.readSBMLFromFile(path)  # libsbml.SBMLDocument
    doc = promote_sbo_to_rdf(doc)
    g = parse_annotations(doc)

