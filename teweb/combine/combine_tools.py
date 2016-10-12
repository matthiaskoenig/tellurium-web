"""
Helper functions to work with combine archives.
"""
from __future__ import print_function, division
from .models import Archive

import libcombine
import libsbml


def printMetaDataFor(co_archive, location):
    """ Print metadata.

    :param co_archive:
    :param location:
    :return:
    """
    desc = co_archive.getMetadataForLocation(location)
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
        print("\t\t{0} {1}".format(creator.getGivenName(), creator.getFamilyName()))


def printArchive(fileName):
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
        printMetaDataFor(archive, entry.getLocation())

        # the entry could now be extracted via
        # archive.extractEntry(entry.getLocation(), <filename or folder>)

        # or used as string
        # content = archive.extractEntryToString(entry.getLocation());

    archive.cleanUp()


def getEntries(fileName):
    """ Get entries from archive.

    :param fileName:
    :type fileName:
    :return:
    :rtype:
    """
    entries = []

    archive = libcombine.CombineArchive()
    if not archive.initializeFromArchive(str(fileName)):
        print("Invalid Combine Archive")
        return entries

    printMetaDataFor(archive, ".")
    print("Num Entries: {0}".format(archive.getNumEntries()))

    for i in range(archive.getNumEntries()):
        entries.append(archive.getEntry(i))
    return entries


def get_content(archive):
    path = archive.file.path
    print(path)
    printArchive(fileName=path)


if __name__ == "__main__":
    import django
    django.setup()
    archive = Archive.objects.get(pk=10)
    print(archive)
    get_content(archive)




