"""
Functions for reading and writing metadata to COMBINE archives.

A COMBINE archive can include multiple metadata elements adding information about different content files. To
identify the file a metadata element refers to, the rdf:about attribute of the relevant metadata structure should
use the same value as used in the location attribute of the respective Content element

1. Read all RDF triple serializations from the combine archive (could also be turtle, or other formats)
  <content location="metadata.rdf" format="http://identifiers.org/combine.specifications/omex-metadata"/>
  <content location="metadata.ttl" format="http://identifiers.org/combine.specifications/omex-metadata"/>

As part of reading the metadata, all metadata files in the archive are
parsed in an internal representation.

As part of the writing the internal metadata information is serialized to a file.
"""

import tempfile
from rdflib import Graph, URIRef, BNode, Literal
from pprint import pprint
import warnings

try:
    import libcombine
except ImportError:
    import tecombine as libcombine

from combine.rdf.parser import parse_rdf, bind_default_namespaces


from rdflib.namespace import Namespace
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')
DCTERMS = Namespace('http://purl.org/dc/terms/')
BQMODEL = Namespace('http://biomodels.net/model-qualifiers/')


##############################################################

def read_metadata(archive_path):
    """ Reads and parses all the metadata information from given COMBINE archive.

    :param archive_path:
    :return: metadata_dict
    """

    def read_predicate(g, location, predicate):
        """ Only a single entry should exist in the graph directly
        connected to the location.

        :param field:
        :param predicate:
        :return:
        """
        result = None

        for triple in g.triples((URIRef(location), predicate, None)):
            (subj, pred, obj) = triple

            # not terminal node, but linear pathway, follow the trail
            while not isinstance(obj, Literal):
                triples = list(g.triples((obj, None, None)))
                if len(triples) == 0:
                    warnings.warn("Something went wrong !")
                    return str(obj)
                    break

                (subj, pred, obj) = triples[0]

            result = str(obj)

        return result


    def read_predicate_list(g, location, predicate):
        """ Multiple entries can exist

        :param field:
        :param predicate:
        :return: list
        """
        results = []

        for triple in g.triples((URIRef(location), predicate, None)):
            (subj, pred, obj) = triple

            # not terminal node, but linear pathway, follow the trail
            while not isinstance(obj, Literal):
                triples = list(g.triples((obj, None, None)))
                if len(triples) == 0:
                    warnings.warn("Something went wrong !")
                    return str(obj)
                    break

                (subj, pred, obj) = triples[0]

            results.append(str(obj))
        return results

    def read_creators(g, location):
        """

        :param g:
        :return:
        """
        creators = []
        for triple in g.triples((URIRef(location), DCTERMS.creator, None)):
            (subj, pred, obj) = triple

            info = {}
            for (s,p,o) in g.triples((obj, VCARD.hasEmail, None)):
                info["email"] = str(o)

            for (s,p,o) in g.triples((obj, VCARD["organization-name"], None)):
                info["organisation"] = str(o)

            for (s,p,o) in g.triples((obj, VCARD.hasName, None)):
                for (s2, p2, o2) in g.triples((o, VCARD["family-name"], None)):
                    info["familyName"] = str(o2)
                for (s2, p2, o2) in g.triples((o, VCARD["given-name"], None)):
                    info["givenName"] = str(o2)
            creators.append(info)

        return creators

    def read_triples(g):
        """ Reads the triples in the graph.

        :param g:
        :return:
        """
        triples = []
        for (s,p,o) in g.triples((None, None, None)):
            triples.append((str(s), str(p), str(o)))

        return triples

    metadata_dict = {}
    graph_dict = read_rdf_graphs(archive_path=archive_path)

    for location, g in graph_dict.items():
        metadata = {}
        metadata['about'] = location
        metadata['description'] = read_predicate(g, location, predicate=DCTERMS.description)
        metadata['created'] = read_predicate(g, location, predicate=DCTERMS.created)
        metadata['modified'] = read_predicate_list(g, location, DCTERMS.modified)
        metadata['creators'] = read_creators(g, location)
        metadata['triples'] = read_triples(g)

        metadata_dict[location] = metadata

    # pprint(metadata_dict)
    return metadata_dict


def read_rdf_graphs(archive_path, debug=False):
    """ Reads all the RDF subgraphs for the locations in the COMBINE archive.

    :param archive_path:
    :return:
    """
    # FIXME: this should be done for all zip entries!
    # Resources could be annotated but not listed in the manifest

    omex = libcombine.CombineArchive()
    if omex.initializeFromArchive(archive_path) is None:
        print("Invalid Combine Archive: {}", archive_path)
        return None

    # find metadata locations and parse the information
    graphs = []
    locations = []
    for i in range(omex.getNumEntries()):
        entry = omex.getEntry(i)

        # normalize the location of the entries
        location = entry.getLocation()
        print(location)
        if (len(location) > 1) and (not location.startswith(".")):
            location = "./{}".format(location)

        if len(location) == 0:
            location = "."

        locations.append(location)
        format = entry.getFormat()

        # read metadata from metadata files
        if format.endswith("omex-metadata"):
            print(location, entry.getLocation())

            # extract to temporary file
            suffix = location.split('/')[-1]
            tmp = tempfile.NamedTemporaryFile("w", suffix=suffix)
            omex.extractEntry(entry.getLocation(), tmp.name)

            g = parse_rdf(tmp.name, debug=True)
            # close the tmp file
            tmp.close()
            graphs.append(g)

    # graph lookup via locations
    graph_dict = {}

    if len(graphs) > 0:
        # Merge the graphs from multiple files
        # FIXME: this is poor mans merging which can result in blank node collisions !
        # see: https://rdflib.readthedocs.io/en/stable/merging.html

        g = graphs[0]
        for k, g_next in enumerate(graphs):
            if k > 0:
                g += g_next

        # print(g.serialize(format='turtle').decode("utf-8"))

        # Split the graphs for the different locations, i.e.,
        # single graphs for the various resources

        for location in locations:
            gloc = transitive_subgraph(g, start=URIRef(location))
            bind_default_namespaces(gloc)
            graph_dict[location] = gloc

            if debug:
                print('-' * 80)
                print("PARSE METADATA:", location)
                print('-' * 80)
                print(gloc.serialize(format='turtle').decode("utf-8"))
    else:
        print("No graphs parsed.")

    omex.cleanUp()
    return graph_dict


def transitive_subgraph(g, start, gloc=None):
    """ Calculates recursively the transitive subgraph from given starting subject.

    :param g: master graph to search in
    :param start: starting subject.
    :param gloc: resulting transitive subgraph
    :return:
    """
    if gloc is None:
        gloc = Graph()

    # Search next edges & add to graph
    triples = list(g.triples((start, None, None)))
    gloc += triples

    # recursive adding of triples (starting now from object)
    for (subj, pred, obj) in triples:
        transitive_subgraph(g, start=obj, gloc=gloc)

    return gloc


def write_metadata(metadata, file_path):

    # FIXME: remove Description for emtpy tags (modfied, created
    # rdf: parseType = "Resource"
    s = metadata.serialize(format='pretty-xml')
    print("-" * 80)
    print(s.decode("utf-8"))
    print("-" * 80)


########################################################################
if __name__ == "__main__":

    metadata = read_metadata("../testdata/rdf/L1V3_vanderpol-sbml.omex")
    pprint(metadata)

    print("-" * 80)

    metadata = read_metadata("../testdata/rdf/CombineArchiveShowCase.omex")
    pprint(metadata)

    # write_metadata(metadata, file_path=None)
