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

Additional information:
http://purl.org/NET/mediatypes/application/rdf+xml


"""

import tempfile
from rdflib import Graph, URIRef, BNode, Literal
from pprint import pprint
import warnings
import zipfile

from combine.comex import read_manifest_entries

from combine.rdf.parser import VCARD, DCTERMS, BQMODEL, BQBIOL, RDF
from combine.rdf.parser import parse_rdf, bind_default_namespaces


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


    def _objects_in_bag(triple):
        """ Check if object sits in Bag.

        :param triple:
        :return:
        """
        (subj, pred, obj) = triple

        # outgoing edges
        triples = list(g.triples((obj, None, None)))
        is_bag = len([(s, p, o) for (s, p, o) in triples if p == RDF.type]) > 0

        if is_bag:
            # return list entries
            return [(s, p, o) for (s, p, o) in triples if p != RDF.type]
        else:
            return [(subj, pred, obj)]


    def read_creators(g, location):
        """ Read the creators from given graph

        :param g:
        :return:
        """
        creators = []
        for triple in g.triples((URIRef(location), DCTERMS.creator, None)):

            # get the object in the bag (if not in bag triple is returned)
            (subj, pred, obj) = _objects_in_bag(triple)[0]

            # print("*" * 80)
            # print((subj, pred, obj))

            info = {}

            # email
            for (s, p, o) in list(g.triples((obj, VCARD.hasEmail, None))) + list(g.triples((obj, VCARD.email, None))):
                info["email"] = str(o)

            # organization
            for (s, p, o) in g.triples((obj, VCARD["organization-name"], None)):
                info["organisation"] = str(o)

            # names
            for (s, p, o) in list(g.triples((obj, VCARD.hasName, None))) + list(g.triples((obj, VCARD.n, None))):
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
        for (s, p, o) in g.triples((None, None, None)):
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

    return metadata_dict


def read_rdf_graphs(archive_path, debug=False):
    """ Reads all the RDF subgraphs for the locations in the COMBINE archive.

    :param archive_path:
    :return:
    """
    # find metadata locations
    entries_dict = read_manifest_entries(archive_path)
    metadata_paths = []
    for location, entry in entries_dict.items():
        format = entry.get('format')
        if format and format.endswith("omex-metadata"):
            path = location
            path = path.replace("./", "")
            metadata_paths.append(path)

    # read metadata from metadata files
    graphs = []
    with zipfile.ZipFile(archive_path) as z:
        for path in metadata_paths:

            try:
                # raise KeyError if path not in zip archive
                zipinfo = z.getinfo(path)

                # extract to temporary file
                suffix = path.split('/')[-1]
                tmp = tempfile.NamedTemporaryFile("wb", suffix=suffix)
                tmp.write(z.read(path))
                tmp.seek(0)

                g = parse_rdf(location=tmp.name, debug=False)

                tmp.close()
                graphs.append(g)

            except KeyError:
                warnings.warn("No '{}' in zip, despite listed in manifest: {}".format(path, archive_path))

    # graph dictionary based on locations
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
        for location in entries_dict.keys():
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

    return graph_dict


def transitive_subgraph(g, start, gloc=None):
    """ Calculates recursively the transitive subgraph from given starting subject.

    :param g: master graph to search in
    :param start: starting subject.
    :param gloc: resulting transitive subgraph
    :return:
    """
    created = False
    if gloc is None:
        gloc = Graph()
        created = True

    # Search next edges & add to graph
    # triples where the subject starts with location
    if created and str(start) != ".":
        triples = []
        for (s, p, o) in g:
            if s.startswith(start):
                gloc.add((s, p, o))
                triples.append((s, p, o))
    # identity
    else:
        triples = list(g.triples((start, None, None)))
        gloc += triples

    # recursive adding of triples (starting now from object)
    for (subj, pred, obj) in triples:
        transitive_subgraph(g, start=obj, gloc=gloc)

    return gloc


########################################################################
if __name__ == "__main__":

    metadata = read_metadata("../testdata/rdf/smith_chase_nokes_shaw_wake_2004.omex")
    pprint(metadata['./smith_chase_nokes_shaw_wake_2004.cellml'])

    print("-" * 80)

    # metadata = read_metadata("../testdata/rdf/CombineArchiveShowCase.omex")
    # pprint(metadata)

    # metadata = read_metadata("../testdata/rdf/BIOMD0000000176.omex")
    # pprint(metadata)


