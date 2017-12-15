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

import os
import tempfile
from pprint import pprint
from rdflib import Graph, URIRef


try:
    import libcombine
except ImportError:
    import tecombine as libcombine


from combine.rdf.parser import parse_rdf

def read_metadata(archive_path):
    """ Reads and parses all the metadata information from given COMBINE archive.


    :param archive_path:
    :return: metadata
    """
    metadata = None

    omex = libcombine.CombineArchive()
    if omex.initializeFromArchive(archive_path) is None:
        print("Invalid Combine Archive: {}", archive_path)
        return None

    # find metadata locations and parse the information
    graphs = []
    locations = []
    for i in range(omex.getNumEntries()):
        entry = omex.getEntry(i)
        location = entry.getLocation()
        if len(locations) > 0:
            locations.append("./{}".format(location))
        else:
            locations.append(".")
        format = entry.getFormat()

        # read metadata from metadata files
        if format.endswith("omex-metadata"):

            # extract to temporary file
            suffix = location.split('/')[-1]
            tmp = tempfile.NamedTemporaryFile("w", suffix=suffix)
            omex.extractEntry(location, tmp.name)

            g = parse_rdf(tmp.name)
            # close the tmp file
            tmp.close()
            graphs.append(g)

    # Merge the graphs from multiple files
    # FIXME: this is poor mans merging which can result in blank node collisions !
    # see: https://rdflib.readthedocs.io/en/stable/merging.html
    g = graphs[0]
    for k, g_next in enumerate(graphs):
        if k > 0:
            g += g_next

    print(g.serialize(format='turtle').decode("utf-8"))

    # Split the graphs for the different locations, i.e.,
    # single graphs for the various resources
    graph_dict = {}
    for location in locations:
        print('-' * 80)
        print("PARSE METADATA:", location)
        print('-' * 80)

        gloc = Graph()
        gloc += g.triples((URIRef(location), None, None))
        print(gloc.serialize(format='turtle').decode("utf-8"))

        # dcterms:description
        # dcterms:created
        # dcterms:modified
        # dcterms:creator + vcard information

    omex.cleanUp()
    return metadata


def write_metadata(metadata, file_path):

    # FIXME: remove Description for emtpy tags (modfied, created
    # rdf: parseType = "Resource"
    s = metadata.serialize(format='pretty-xml')
    print("-" * 80)
    print(s.decode("utf-8"))
    print("-" * 80)


def metadata_for_location(co_archive, location):
    """ Returns the metadata for given location.

        :param co_archive:
        :param location:
        :return:
        """

    desc = co_archive.getMetadataForLocation(location)  # type: libcombine.OmexDescription
    if desc.isEmpty():
        return None

    info = dict()  # type: dict
    info['about'] = desc.getAbout()
    info['description'] = desc.getDescription()
    info['created'] = desc.getCreated().getDateAsString()
    info['creators'] = []
    info['modified'] = []

    for i in range(desc.getNumModified()):
        modified = desc.getModified(i).getDateAsString()
        info['modified'].append(modified)

    for i in range(desc.getNumCreators()):
        vcard = desc.getCreator(i)  # type: libcombine.VCard
        info['creators'].append(
            {
                'givenName': vcard.getGivenName(),
                'familyName': vcard.getFamilyName(),
                'email': vcard.getEmail(),
                'organisation': vcard.getOrganization()
             }
        )
    return info


if __name__ == "__main__":
    # TODO: implement
    omex_path = "../testdata/rdf/L1V3_vanderpol-sbml.omex"
    metadata = read_metadata(omex_path)
    # pprint(metadata)
    # write_metadata(metadata, file_path=None)
