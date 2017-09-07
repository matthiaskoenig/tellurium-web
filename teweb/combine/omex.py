"""
Helper functions to work with combine archives
and omex files.
"""
import os
try:
    import libcombine
except ImportError:
    import tecombine as libcombine


def metadata_for_location(co_archive, location):
    """ Returns the metadata for given location.

        :param co_archive:
        :param location:
        :return:
        """
    info = ""
    desc = co_archive.getMetadataForLocation(location)
    if desc.isEmpty():
        info += "no metadata for '{0}'".format(location)
        return info

    info += "metadata for '{0}':\n".format(location)
    info += "\tCreated : {0}\n".format(desc.getCreated().getDateAsString())
    for i in range(desc.getNumModified()):
        info += "\tModified : {0}\n".format(desc.getModified(i).getDateAsString())

    info += "\tCreators: {0}".format(desc.getNumCreators())
    for i in range(desc.getNumCreators()):
        creator = desc.getCreator(i)
        info += "\t\t{0} {1}".format(creator.getGivenName(), creator.getFamilyName())
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
        printMetaDataFor(archive, entry.getLocation())

        # the entry could now be extracted via
        # archive.extractEntry(entry.getLocation(), <filename or folder>)

        # or used as string
        # content = archive.extractEntryToString(entry.getLocation());

    archive.cleanUp()


def get_content(archive):
    path = archive.file.path
    print(path)
    print_archive(fileName=path)
