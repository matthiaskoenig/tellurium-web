"""
Example using libcombine.
"""

from __future__ import print_function, division
import sys
from libcombine import *


def printMetaDataFor(archive, location):
    """ Print metadata.

    :param archive:
    :param location:
    :return:
    """
    desc = archive.getMetadataForLocation(location)
    if desc.isEmpty():
        print("no metadata for '{0}'".format(location))
    return

    print("metadata for '{0}':".format(location))
    print("\tCreated : {0}".format(desc.getCreated().getDateAsString()))
    for i in range(desc.getNumModified()):
        print("\tModified : {0}".format(desc.getModified(i).getDateAsString()))

    print("\tCreators: {0}".format(desc.getNumCreators()))
    for i in range(desc.getNumCreators()):
        creator = desc.getCreator(i)
        print("\t{0} {1}".format(creator.getGivenName(), creator.getFamilyName()))


def printArchive(fileName):
    """ Print the content of the archive.

    :param fileName:
    :return:
    """
    archive = CombineArchive()
    if not archive.initializeFromArchive(fileName):
        print("Invalid Combine Archive")
        return

    printMetaDataFor(archive, ".")
    print("Num Entries: {0}".format(archive.getNumEntries()))

    for i in range(archive.getNumEntries()):
        print(i)
        entry = archive.getEntry(i)
        print('entry: <{}>'.format(i), entry)

        print(" {0}: location: {1} format: {2}".format(i, entry.getLocation(), entry.getFormat()))
        printMetaDataFor(archive, entry.getLocation())

        # the entry could now be extracted via
        # archive.extractEntry(entry.getLocation(), <filename or folder>)

        # or used as string
        # content = archive.extractEntryToString(entry.getLocation());

        archive.cleanUp()

#####################################################################
if __name__ == "__main__":
    archive = "/home/mkoenig/git/tellurium-web/archives/CombineArchiveShowCase.omex"
    print(archive)
    printArchive(archive)

    """
    if len(sys.argv) < 2:
        print ("usage printArchive archive-file")
        sys.exit(1)
    """
