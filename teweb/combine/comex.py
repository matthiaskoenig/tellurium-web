"""
Helper functions to work with combine archives
and omex files.
"""

import libcombine
# FIXME: this is a bugfix for https://github.com/sbmlteam/libCombine/issues/15
import importlib
importlib.reload(libcombine)


def short_format(format):
    """ Returns short format string for given full format string.

    :param format:
    :return:
    """
    tokens = format.split("/")
    short = tokens[-1].split('.')[0]
    short = short.replace('+xml', '')
    return short


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


def print_metadata(co_archive, location):
    """ Print metadata.

    :param co_archive:
    :param location:
    :return:
    """
    info = metadata_for_location(co_archive=co_archive, location=location)
    print(info)


def print_archive(fileName):
    """ Print the content of the archive.

    :param fileName:
    :return:
    """
    print(fileName)
    archive = libcombine.CombineArchive()
    if not archive.initializeFromArchive(str(fileName)):
        print("Invalid Combine Archive")
        return

    printMetaDataFor(archive, ".")
    print("Num Entries: {0}".format(archive.getNumEntries()))

    for i in range(archive.getNumEntries()):
        print(i)
        entry = archive.getEntry(i)
        print('entry: <{}>'.format(i), entry)

        print(" {0}: location: {1} format: {2}".format(i, entry.getLocation(), entry.getFormat()))
        print_metadata(archive, entry.getLocation())

        # the entry could now be extracted via
        # archive.extractEntry(entry.getLocation(), <filename or folder>)

        # or used as string
        # content = archive.extractEntryToString(entry.getLocation());

    archive.cleanUp()


def get_content(archive):
    path = archive.file.path
    print(path)
    print_archive(fileName=path)
