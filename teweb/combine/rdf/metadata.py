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

try:
    import libcombine
except ImportError:
    import tecombine as libcombine


def parse_metadata(metadata_locations):
    # TODO: implement
    pass


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
    parse_metadata()
