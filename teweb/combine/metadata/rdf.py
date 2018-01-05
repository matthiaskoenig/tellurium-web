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


Module for parsing semantic tripples.
Either as RDF (*.rdf) or as Turtle (*.ttl).


RDF is a graph where the nodes are URI references, Blank Nodes or Literals, in RDFLib represented by the classes URIRef, BNode, and Literal.
URIRefs and BNodes can both be thought of as resources, such a person, a company, a web-site, etc.
A BNode is a node where the exact URI is not known. URIRefs are also used to represent the properties/predicates in the RDF graph.
Literals represent attribute values, such as a name, a date, a number, etc.

"""
import os
import warnings
import zipfile
import tempfile
from pprint import pprint

import rdflib
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib.util import guess_format
from rdflib.namespace import Namespace, RDF

from combine.utils import comex

##########################################################################
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')
VCARD_OLD = Namespace('http://www.w3.org/2001/vcard-rdf/3.0#')
DCTERMS = Namespace('http://purl.org/dc/terms/')
DCELEMENTS = Namespace('http://purl.org/dc/elements/1.1/')
BQMODEL = Namespace('http://biomodels.net/model-qualifiers/')
BQBIOL = Namespace('http://biomodels.net/biology-qualifiers/')
##########################################################################


def bind_default_namespaces(g):
    """ Bind the namespace prefixes in graph

    :param g:
    :return:
    """
    g.bind(prefix="vCard", namespace=URIRef("http://www.w3.org/2006/vcard/ns#"))
    g.bind(prefix="vCardOld", namespace=URIRef('http://www.w3.org/2001/vcard-rdf/3.0#'))
    g.bind(prefix="dcterms", namespace=URIRef("http://purl.org/dc/terms/"))
    g.bind(prefix="dcelements", namespace=URIRef("http://purl.org/dc/elements/1.1/"))
    g.bind(prefix="bqmodel", namespace=URIRef("http://biomodels.net/model-qualifiers/"))
    g.bind(prefix="bqbiol", namespace=URIRef("http://biomodels.net/biology-qualifiers/"))


def fix_path_prefix(el, prefix):
    """ Fix prefix via replacement to get relative paths in triples. """
    el_str = str(el)

    # fix relative paths
    if el_str.startswith(prefix):

        # print("replacing prefix:", prefix)
        el_str = el_str.replace(prefix, '')
        if el_str == "":
            el_str = "."
        elif el_str.startswith("#"):
            pass
        else:
            el_str = "./" + el_str
        # create correct node type
        if isinstance(el, BNode):
            el = BNode(el_str)
        elif isinstance(el, URIRef):
            el = URIRef(el_str)
        elif isinstance(el, Literal):
            el = Literal(el_str)

    return el


def parse_rdf(debug=False, **kwargs):
    """ Parses the rdf in graph.

    location: file_path
    data: string data
    """
    path = kwargs['location']

    # file prefix to replace for relative paths
    prefixes = ["file://{}/".format(os.path.abspath(os.path.dirname(path))),  # absolute file prefix
                "./{}".format(os.path.basename(path))]  # relative prefixes in combined annotations

    # parse RDF graph
    g = rdflib.Graph()
    format = guess_format(path)
    g.parse(format=format, **kwargs)

    if debug:
        print("-" * 80)
        print("File prefix:", prefixes)
        print("Format:", format)
        print("Statements: %s" % len(g))
        print("-" * 80)

    def fix_email(obj):
        """ Fixing wrong parsing of emails. """
        # remove email prefix
        obj_str = str(obj)
        for prefix in prefixes:
            obj_str = obj_str.replace(prefix, '')
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
        for prefix in prefixes:
            subj = fix_path_prefix(subj, prefix)
            pred = fix_path_prefix(pred, prefix)
            obj = fix_path_prefix(obj, prefix)

        # add fixed triples
        g2.add((subj, pred, obj))
        if debug:
            print((subj, pred, obj))

    # Serializing the graph
    if debug:
        s2 = g2.serialize(format='pretty-xml')
        print(s2.decode("utf-8"))

        print("\n\n")

        s2 = g2.serialize(format='turtle')
        print(s2.decode("utf-8"))

    return g2


##############################################################
# WRITE METADATA
##############################################################
def create_metadata(archive, rdf_format, debug=False):
    """ Creates the metadata for the current archive.

    This takes all the metadata from all archive entries and serializes
    it.
    """
    g = Graph()
    bind_default_namespaces(g)

    for entry in archive.entries.order_by('location'):

        # Add the metadata triples
        md_serializer = MetaDataRDFSerializer(location=entry.location, metadata=entry.metadata)
        g_meta = md_serializer.get_rdf_triples()
        for (s, p, o) in g_meta:
            g.add((s, p, o))

    if debug:
        print("-" * 80)
        print(g.serialize(format='turtle').decode("utf-8"))
        print("-" * 80)

    return g.serialize(format=rdf_format).decode("utf-8")


def get_element(info_str, type_str):
    """ Helper function for casting. """
    if type_str == "<class 'rdflib.term.URIRef'>":
        return URIRef(info_str)
    elif type_str == "<class 'rdflib.term.BNode'>":
        return BNode(info_str)
    elif type_str == "<class 'rdflib.term.Literal'>":
        return Literal(info_str)
    else:
        raise ValueError

class MetaDataRDFSerializer(object):
    """
    RDF serialization of the metadata information.
    This creates the triples and adds them to graph.
    """

    def __init__(self, location, metadata, g=None):
        self.location = location
        self.metadata = metadata
        self.g = g
        if self.g is None:
            self.g = Graph()
            bind_default_namespaces(self.g)

    def get_rdf_triples(self):
        """ Get all the triples for the metadata information. """
        self._add_created_rdf_triples()
        self._add_modified_rdf_triples()
        self._add_description_rdf_triples()
        self._add_creators_rdf_triples()
        self._add_triples()

        return self.g

    def _add_created_rdf_triples(self):
        """ Gets triple for a new created tag.

        <dcterms:created rdf:parseType="Resource">
            <dcterms:W3CDTF>2017-12-28T16:23:43Z</dcterms:W3CDTF>
        </dcterms:created>
        """
        if isinstance(self.metadata, dict):
            created = self.metadata.get("created")
        else:
            created = self.metadata.created
        if created:
            bnode = BNode()
            self.g.add((URIRef(self.location), DCTERMS.created, bnode))
            self.g.add((bnode, DCTERMS.W3CDTF, Literal(created)))

    def _add_modified_rdf_triples(self):
        """ Gets triple for a modified timestamp.

        <dcterms:modified rdf:parseType="Resource">
            <dcterms:W3CDTF>2017-12-28T16:23:43Z</dcterms:W3CDTF>
        </dcterms:modified>
        """
        if isinstance(self.metadata, dict):
            for modified in self.metadata.get("modified"):
                bnode = BNode()
                self.g.add((URIRef(self.location), DCTERMS.modified, bnode))
                self.g.add((bnode, DCTERMS.W3CDTF, Literal(modified)))
        else:
            for modified in self.metadata.modified.all():
                bnode = BNode()
                self.g.add((URIRef(self.location), DCTERMS.modified, bnode))
                self.g.add((bnode, DCTERMS.W3CDTF, Literal(modified)))


    def _add_description_rdf_triples(self):
        """ Gets triple for description.

        <dcterms:description>Information to create archive metadata</dcterms:description>
        """
        if isinstance(self.metadata, dict):
            description = self.metadata.get("description")
        else:
            description = self.metadata.description
        if description:
            self.g.add((URIRef(self.location), DCTERMS.description, Literal(description)))

    def _add_creators_rdf_triples(self):
        """ Gets triples for creator.

        <dcterms:creator rdf:parseType="Resource">
            <vCard:hasName rdf:parseType="Resource">
                <vCard:family-name>Bergmann</vCard:family-name>
                <vCard:given-name>Frank</vCard:given-name>
            </vCard:hasName><vCard:hasEmail rdf:resource="fbergmann@caltech.edu"/>
            <vCard:organization-name>Caltech</vCard:organization-name>
        </dcterms:creator>
        """
        if isinstance(self.metadata, dict):
            for creator in self.metadata.get('creators'):
                bnode1 = BNode()

                self.g.add((URIRef(self.location), DCTERMS.creator, bnode1))
                self.g.add((bnode1, DCTERMS['organization-name'], Literal(creator.get("organisation"))))
                self.g.add((bnode1, DCTERMS.hasEmail, Literal(creator.get("email"))))
                bnode2 = BNode()
                self.g.add((bnode1, DCTERMS.hasName, bnode2))
                self.g.add((bnode2, DCTERMS['family-name'], Literal(creator.get("givenName"))))
                self.g.add((bnode2, DCTERMS['given-name'], Literal(creator.get("familyName"))))
        else:
            for creator in self.metadata.creators.all():
                bnode1 = BNode()

                self.g.add((URIRef(self.location), DCTERMS.creator, bnode1))
                self.g.add((bnode1, DCTERMS['organization-name'], Literal(creator.organisation)))
                self.g.add((bnode1, DCTERMS.hasEmail, Literal(creator.email)))
                bnode2 = BNode()
                self.g.add((bnode1, DCTERMS.hasName, bnode2))
                self.g.add((bnode2, DCTERMS['family-name'], Literal(creator.last_name)))
                self.g.add((bnode2, DCTERMS['given-name'], Literal(creator.first_name)))

    def _add_triples(self):
        """ Adds the remaining triples. """
        if isinstance(self.metadata, dict):
            # Write all annotation triples
            for triples in [self.metadata.get("triples"), self.metadata.get("bm_triples")]:
                for triple in triples:
                    s = get_element(triple[0], triple[1])
                    p = get_element(triple[2], triple[3])
                    o = get_element(triple[4], triple[5])
                    self.g.add((s, p, o))
        else:
            # Write all annotation triples
            for triple in self.metadata.triples.all():
                s = get_element(triple.subject, triple.subject_type)
                p = get_element(triple.predicate, triple.predicate_type)
                o = get_element(triple.object, triple.object_type)
                self.g.add((s, p, o))


##############################################################
# READ METADATA
##############################################################

def read_metadata(archive_path):
    """ Reads and parses all the metadata information from given COMBINE archive.

    :param archive_path:
    :return: metadata_dict
    """
    metadata_dict = {}
    graph_dict = read_rdf_graphs(archive_path=archive_path)

    for location, g in graph_dict.items():
        metadata_dict[location] = read_metadata_from_graph(location, g)

    return metadata_dict


def read_metadata_from_graph(location, g):
    """ Reads the metadata from given graph

    :param location:
    :param g:
    :return:
    """
    metadata = {}
    metadata['about'] = location
    metadata['description'] = read_predicate(g, location, predicate=DCTERMS.description, multiple=False)
    metadata['created'] = read_predicate(g, location, predicate=DCTERMS.created, multiple=False)
    metadata['modified'] = read_predicate(g, location, predicate=DCTERMS.modified, multiple=True)
    metadata['creators'] = read_creators(g, location)
    metadata['bm_triples'] = biomodels_triples_from_graph(g, location)
    metadata['triples'] = django_triples_from_graph(g)
    return metadata


def read_creators(g, location, delete=True):
    """ Read the creators from given graph

    :param g:
    :return:
    """
    creators = []
    deleted_triples = []
    for triple in list(g.triples((URIRef(location), DCTERMS.creator, None))) + list(g.triples((URIRef(location), DCELEMENTS.creator, None))):
        deleted_triples.append(triple)
        # get the object in the bag (if not in bag triple is returned)
        for (subj, pred, obj) in _objects_in_bag(g, triple, deleted_triples=deleted_triples):
            # (subj, pred, obj) = _objects_in_bag(g, triple, deleted_triples=deleted_triples)[0]
            info = {}

            # email
            for (s, p, o) in list(g.triples((obj, VCARD.hasEmail, None))) + list(g.triples((obj, VCARD.email, None))) + list(g.triples((obj, VCARD_OLD.EMAIL, None))):
                info["email"] = str(o)
                deleted_triples.append((s, p, o))

            # organization
            for (s, p, o) in g.triples((obj, VCARD["organization-name"], None)):
                info["organisation"] = str(o)
                deleted_triples.append((s, p, o))

            for (s, p, o) in list(g.triples((obj, VCARD.org, None))) + list(g.triples((obj, VCARD_OLD.ORG, None))):
                deleted_triples.append((s, p, o))
                for (s2, p2, o2) in list(g.triples((o, VCARD["organization-name"], None))) + list(g.triples((o, VCARD_OLD["Orgname"], None))):
                    info["organisation"] = str(o2)
                    deleted_triples.append((s2, p2, o2))

            # names
            for (s, p, o) in list(g.triples((obj, VCARD.hasName, None))) + list(g.triples((obj, VCARD.n, None))) + list(g.triples((obj, VCARD_OLD.N, None))):
                deleted_triples.append((s, p, o))
                for (s2, p2, o2) in list(g.triples((o, VCARD["family-name"], None))) + list(g.triples((o, VCARD_OLD["Family"], None))):
                    info["familyName"] = str(o2)
                    deleted_triples.append((s2, p2, o2))
                for (s2, p2, o2) in list(g.triples((o, VCARD["given-name"], None))) + list(g.triples((o, VCARD_OLD["Given"], None))):
                    info["givenName"] = str(o2)
                    deleted_triples.append((s2, p2, o2))

            creators.append(info)

    # delete triples
    for triple in deleted_triples:
        g.remove(triple)

    return creators


def read_predicate(g, location, predicate, multiple=True, delete=True):
    """ Multiple entries can exist

    :param field:
    :param predicate:
    :return: list
    """
    results = []
    deleted_triples = []

    for triple in g.triples((URIRef(location), predicate, None)):
        (subj, pred, obj) = triple
        deleted_triples.append(triple)

        # not terminal node, but linear pathway, follow the trail
        while not isinstance(obj, Literal):
            triples = list(g.triples((obj, None, None)))
            deleted_triples.extend(triples)
            if len(triples) == 0:
                warnings.warn("Something went wrong !")
                return str(obj)
                break

            (subj, pred, obj) = triples[0]

        results.append(str(obj))

    # delete triples
    for triple in deleted_triples:
        g.remove(triple)

    if multiple:
        # list of entries returned
        return results
    else:
        # single entry or None returned
        if len(results)>0:
            return results[0]
        else:
            return None


def biomodels_triples_from_graph(g, location):
    # consumes the biomodels triples from the rdf graph
    triples = []

    # handle the bags for the triples
    deleted_triples = []
    for triple in g.triples((URIRef(location), None, None)):
        (s_root, p_root, o_root) = triple

        # this is a biomodel qualifier
        if str(p_root).startswith("http://biomodels.net/"):

            deleted_triples.append(triple)
            # get the object in the bag (if not in bag triple is returned)
            for (s, p, o) in _objects_in_bag(g, triple, deleted_triples=deleted_triples):

                # fix old go in object: 'obo.go' -> 'go', 'obo.chebi', ...
                if isinstance(o, rdflib.URIRef):
                    if str(o).startswith('http://identifiers.org/obo.'):
                        o = rdflib.URIRef(str(o).replace('http://identifiers.org/obo.', 'http://identifiers.org/'))

                triples.append(
                    _django_triple((s, p, o))
                )

    # delete triples
    for triple in deleted_triples:
        g.remove(triple)

    return triples



def django_triples_from_graph(g):
    """ Reads the django triples from the given graph.

    :param g:
    :return:
    """
    triples = []
    for triple in g:
        triples.append(_django_triple(triple))

    return triples


def _django_triple(triple):
    """ Creates the django triple from RDF triple. """
    s, p, o = triple
    return [str(el) for el in (s, type(s), p, type(p), o, type(o))]


def _objects_in_bag(g, triple, deleted_triples=None):
    """ Check if object sits in Bag.

    :param triple:
    :return:
    """
    (subj, pred, obj) = triple

    # outgoing edges
    triples = list(g.triples((obj, None, None)))
    if deleted_triples is not None:
        deleted_triples.extend(triples)
    is_bag = len([(s, p, o) for (s, p, o) in triples if p == RDF.type]) > 0

    if is_bag:
        # return list entries with fixed subject and predicate
        objects = [(subj, pred, o) for (s, p, o) in triples if p != RDF.type]
    else:
        return [(subj, pred, obj)]

    # fix the subjects

    return objects


def read_rdf_graphs(archive_path, debug=False):
    """ Reads all the RDF subgraphs for the locations in the COMBINE archive.

    :param archive_path:
    :return:
    """
    # find metadata locations
    # FIXME: here a second time the archive entries are parsed ! Reuse
    entries_dict = comex.EntryParser.read_manifest_entries(archive_path)
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
            gloc = _transitive_subgraph(g, start=URIRef(location))
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


def _transitive_subgraph(g, start, gloc=None):
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
        _transitive_subgraph(g, start=obj, gloc=gloc)

    return gloc


########################################################################
if __name__ == "__main__":

    metadata = read_metadata("../tests/testdata/metadata/metadata_minimal.omex")
    # metadata = read_metadata("../tests/testdata/archives/smith_chase_nokes_shaw_wake_2004.omex")
    pprint(metadata['.'])

    print("-" * 80)

    # metadata = read_metadata("../testdata/rdf/CombineArchiveShowCase.omex")
    # pprint(metadata)

    # metadata = read_metadata("../testdata/rdf/BIOMD0000000176.omex")
    # pprint(metadata)


    f1 = "../tests/testdata/metadata/metadata1.rdf"
    f2 = "../tests/testdata/metadata/metadata2.rdf"
    f3 = "../tests/testdata/metadata/metadata_minimal.rdf"

    # parse_rdf(location=f3, debug=True)

