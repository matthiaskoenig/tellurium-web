"""
Helper functions to work with combine archives and zip files.

Getting information out of the files.
"""
import os
import json
import zipfile

try:
    import libcombine
except ImportError:
    import tecombine as libcombine

try:
    import libsedml
except ImportError:
    import tesedml as libsedml


# FIXME: this is a bugfix for https://github.com/sbmlteam/libCombine/issues/15
import importlib
importlib.reload(libcombine)

from collections import namedtuple
TagInfo = namedtuple("TagInfo", "category name")


def get_omex_file_paths(archive_dirs):
    """ Returns list of given combine archive paths from given list of directories.

    :param archive_dirs:
    :return:
    """

    # list files
    omex_files = []
    for archive_dir in archive_dirs:
        for subdir, dirs, files in os.walk(archive_dir):
            for file in files:
                path = os.path.join(subdir, file)
                if os.path.isfile(path) and (path.endswith('.omex') or path.endswith('.sedx')):
                    omex_files.append(path)
    return omex_files


################################################
# Tag helpers
################################################
def tags_info(archive_path):
    """ Reads the tags info from a given archive.

    :param archive_path:
    :return:
    """
    tags_info = []

    # add the file formats from omex
    omex = libcombine.CombineArchive()
    if omex.initializeFromArchive(archive_path) is None:
        print("Invalid Combine Archive: {}", archive_path)
        return None

    sedml_entries = []
    sbml_entries = []
    for i in range(omex.getNumEntries()):
        entry = omex.getEntry(i)
        format = entry.getFormat()
        location = entry.getLocation()
        format_id = base_format(format)

        if format_id in ['sbml', 'cellml', 'sed-ml', 'sedml', 'sbgn', 'sbol']:
            tags_info.append(
                TagInfo(category='format', name=format_id)
            )
        if format_id == 'sbml':
            sbml_entries.append(entry)
        if format_id in ['sedml', 'sed-ml']:
            sedml_entries.append(entry)

    # add the SBML contents
    # add the SED-ML contents
    for entry in sedml_entries:
        content = omex.extractEntryToString(entry.getLocation())
        doc = libsedml.readSedMLFromString(content)  # type: libsedml.SedDocument
        print(doc)

        for model in doc.getListOfModels():
            language = model.getLanguage()
            if language:
                name = language.split(':')[-1]
                tags_info.append(
                    TagInfo(category='sedml', name='model:{}'.format(name))
                )

        if len(doc.getListOfDataDescriptions()) > 0:
            tags_info.append(
                TagInfo(category='sedml', name='DataDescription')
            )

    omex.cleanUp()
    return tags_info


################################################
# Zip
################################################
def zip_tree_content(path):
    """ Returns the entries of the combine archive zip file.

    These are all files in the zip files. Not all of these
    have to be managed in the entries of the Combine Archive.

    The JSON data is in the following format (jstree)
        tree_data = [
            {"id": "ajson1", "parent": "#", "text": "Simple root node", "state": {"opened": True, "selected": True}},
            {"id": "ajson2", "parent": "#", "text": "Root node 2", "state": {"opened": True}},
            {"id": "ajson3", "parent": "ajson2", "text": "Child 1"},
            {"id": "ajson4", "parent": "ajson2", "text": "Child 2", "icon": "fa fa-play"}
        ]
    :param path:
    :return:
    """
    def find_parent(filename):
        if filename.endswith('/'):
            filename = filename[:-1]
        tokens = filename.split("/")
        if len(tokens) == 1:
            return '#'
        return '/'.join(tokens[:-1]) + '/'

    def find_name(filename):
        splited_file = filename.split("/")
        if splited_file[-1] == "":
            return splited_file[-2]
        return splited_file[-1]


    def node_from_filename(filename):
        node = {}
        node['id'] = filename
        node['parent'] = find_parent(filename)
        node['text'] = find_name(filename)
        if filename.endswith('/'):
            icon = "fa fa-folder fa-fw"
        else:
            icon = "fa fa-file-o fa-fw"
        node['icon'] = icon
        node['state'] = {'opened': True}
        return node

    nodes = {}
    with zipfile.ZipFile(path) as zip:
        # zip.printdir()
        for zip_info in zip.infolist():

            # print(zip_info)
            # zip_info.filename
            # zip_info.date_time
            # zip_info.file_size
            node = node_from_filename(zip_info.filename)
            nodes[node['id']] = node

    # directories do not have to be part of the zip file, so we have to
    # manually add these nodes if they are missing
    length_nodes = 0
    while len(nodes) > length_nodes:
        check_ids = list(nodes.keys())  # make a copy we can iterate over
        length_nodes = len(nodes)
        for nid in check_ids:
            node = nodes[nid]
            parent_id = node['parent']
            if parent_id not in check_ids and parent_id != "#":
                parent_node = node_from_filename(parent_id)
                nodes[parent_id] = parent_node
                #print("Added missing folder node:", parent_id)

    tree_data = [nodes[key] for key in sorted(nodes.keys())]

    return json.dumps(tree_data)


################################################
# Combine Archives
################################################

def entries_info(archive_path):
    """ Creates entries information for given archive.

    :param archive_path:
    :return:
    """

    # read combine archive contents & metadata
    omex = libcombine.CombineArchive()
    if omex.initializeFromArchive(archive_path) is None:
        print("Invalid Combine Archive: {}", archive_path)
        return None

    # add entries
    entries = []
    for i in range(omex.getNumEntries()):
        entry = omex.getEntry(i)
        location = entry.getLocation()
        format = entry.getFormat()
        info = {}
        info['location'] = location
        info['format'] = format
        info['short_format'] = short_format(format)
        info['base_format'] = base_format(format)
        info['master'] = entry.getMaster()
        info['metadata'] = metadata_for_location(omex, location=location)

        entries.append(info)

    # add root information
    format = 'http://identifiers.org/combine.specifications/omex'
    info = {
        'location': '.',
        'format': format,
        'short_format': short_format(format),
        'base_format': base_format(format),
        'metadata': metadata_for_location(omex, '.'),
        'master': None
    }
    entries.append(info)

    omex.cleanUp()
    return entries


def short_format(format):
    """ Returns short format string for given full format string.

    http://identifiers.org/combine.specifications/omex-metadata
    -> omex-metadata

    http://identifiers.org/combine.specifications/sbml.level-3.version-1
    -> sbml.level-3.version-1

    :param format:
    :return:
    """
    tokens = format.split("/")
    return tokens[-1]


def base_format(format):
    """ Returns the base format string for given full format string.

    http://identifiers.org/combine.specifications/omex-metadata
    -> omex-metadata

    http://identifiers.org/combine.specifications/sbml.level-3.version-1
    -> sbml

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


if __name__ == "__main__":
    path = "../../archives/CombineArchiveShowCase.omex"
    tags_info(archive_path=path)
