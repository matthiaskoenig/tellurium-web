"""
Module for working with SBML annotations.
"""
import os
import rdflib
import uuid
import logging
from pprint import pprint

from combine.metadata.rdf import bind_default_namespaces, read_metadata_from_graph
from combine.metadata.rdf import MetaDataRDFSerializer

try:
    import libsbml
except:
    import tesbml as libsbml

logger = logging.getLogger(__name__)


def parse_metadata(path_sbml, prefix=None, promote_sbo=True, ):
    """ Parses the annotations from a given SBML file.
    """
    assert os.path.exists(path_sbml)
    doc = libsbml.readSBMLFromFile(path_sbml)  # libsbml.SBMLDocument
    if promote_sbo:
        # Promote the SBO terms
        doc = promote_sbo_to_rdf(doc)

    metadata_dict = _parse_metadata_from_doc(doc, prefix=prefix)
    return metadata_dict


def _parse_metadata_from_doc(doc: libsbml.SBMLDocument, prefix=None, debug=False) -> dict:
    """ Parses the annotations from a given SBML file.

    :param doc:
    :return:
    """
    metadata_dict = {}

    # iterate over all SBases
    for element in doc.getListOfAllElements():

        annotation = element.getAnnotation()  # type: libsbml.XMLNode
        if annotation:
            metaid = element.getMetaId()
            try:
                location, metadata = _parse_metadata_from_annotation(annotation, metaid=metaid, prefix=prefix)
                if metadata is not None:

                    if debug:
                        ttl = g.serialize(format='turtle').decode("utf-8")
                        print("-" * 80)
                        print(ttl)
                        print("-" * 80)
                        pprint(metadata)

                    metadata_dict[location] = metadata
            except:
                logger.error("Error parsing RDF from annotation on '{}' {}".format(element, element.getAnnotationString()))
                raise

    return metadata_dict


def _parse_metadata_from_annotation(annotation, metaid, prefix):
    """

    :param annotation:
    :param prefix:
    :return:
    """
    # individual metadata graph for every element
    g = rdflib.Graph()
    bind_default_namespaces(g)

    # location of this element
    location = prefix + "#" + metaid

    # parse rdf of element
    rdf_node = annotation.getChild("RDF")  # type: libsbml.XMLNode
    rdf_str = rdf_node.toXMLString()  # type: str
    if not rdf_str:
        return location, None
    else:
        # parse RDF
        g_element = rdflib.Graph()
        g_element.parse(data=rdf_str, format="xml")

        # add triples to graph
        for (s, p, o) in g_element:
            # add prefixes
            if prefix:
                if isinstance(s, rdflib.URIRef) and (str(s).startswith('#')):
                    s = rdflib.URIRef(prefix + str(s))
            g.add((s, p, o))

        # parse metadata from graph
        metadata = read_metadata_from_graph(location, g)
        return location, metadata


def externalize_annotations(path_in, path_out, prefix=None, format="turtle", debug=False):
    """

    :param path_in:
    :param path_out:
    :param prefix:
    :param format: one of the serializer formats, i.e., "turtle", "pretty-xml", ...
    :return:
    """
    metadata_dict = parse_metadata(path_sbml=path_in, prefix=prefix)
    pprint(metadata_dict)

    # Create full RDF graph from individual graphs
    g = None
    for location, metadata in metadata_dict.items():
        # add the triples for current entry
        serializer = MetaDataRDFSerializer(location=location, metadata=metadata, g=g)
        g = serializer.get_rdf_triples()

    # serialize the full graph
    rdf_byte = g.serialize(format=format)
    if debug:
        print("-" * 80)
        print(rdf_byte.decode("utf-8"))
        print("-" * 80)

    with open(path_out, "wb") as f_out:
        f_out.write(rdf_byte)

    return rdf_byte.decode("utf-8")


def promote_sbo_to_rdf(doc: libsbml.SBMLDocument) -> libsbml.SBMLDocument:
    """
    Add the SBOTerms to the RDF.
    Autogenerates metaids if necessary.

    This is a helper function to convert SBOTerms to RDF.

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
                    if uri.endswith(sbo):
                        contains_sbo = True
                        break

            # add the cvterm
            if not contains_sbo:
                # set meta id
                if not element.isSetMetaId():
                    # FIXME: this is not reproducible
                    metaid = "meta_" + str(uuid.uuid4())
                    element.setMetaId(metaid)

                # add cvterm
                uri = "http://identifiers.org/sbo/" + sbo
                cvterm = libsbml.CVTerm()
                cvterm.setQualifierType(libsbml.MODEL_QUALIFIER)
                cvterm.setModelQualifierType(libsbml.BQM_IS)
                cvterm.addResource(uri)
                code = element.addCVTerm(cvterm)

                if code is not libsbml.LIBSBML_OPERATION_SUCCESS:
                    logger.error("Setting SBO CVTerm '{}' on {} failed with {}".format(sbo, element, code))
                    logger.error(libsbml.OperationReturnValue_toString(code))

    return doc


#########################################################
if __name__ == "__main__":
    print(libsbml.getLibSBMLDottedVersion())

    # TODO: fix old obos

    base_path = "./BIOMD0000000012"
    base_path = "./BIOMD0000000176_full/BIOMD0000000176"

    path_in, path_ttl, path_rdf = (base_path + ".xml", base_path + ".ttl", base_path + ".rdf")
    rdf_ttl = externalize_annotations(path_in=path_in, path_out=path_ttl, prefix=path_in, format="turtle")
    rdf_xml = externalize_annotations(path_in=path_in, path_out=path_rdf, prefix=path_in, format="pretty-xml")

    print(rdf_ttl)

    metadata_dict = parse_metadata(path_sbml=path_in, prefix=path_in)
    print('*' * 80)
    pprint(metadata_dict)