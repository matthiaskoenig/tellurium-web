"""
Helper functions to work with combine archives and zip files.

Getting information out of the files.
"""
import os
import json
import zipfile
import warnings

try:
    import libcombine
except ImportError:
    import tecombine as libcombine

from .rdf.metadata import metadata_for_location


def get_omex_file_paths(archive_dirs):
    """ Returns list of given combine archive paths from given list of directories.

    Helper function used for instance for the bulk import of COMBINE archives in the
    database.

    :param archive_dirs: list of directories
    :return: list of omex_files
    """

    omex_files = []
    for archive_dir in archive_dirs:

        if not os.path.exists(archive_dir):
            warnings.warn("Directory does not exist: {}".format(archive_dir))

        for subdir, dirs, files in os.walk(archive_dir):
            for file in files:
                path = os.path.join(subdir, file)
                if os.path.isfile(path) and (path.endswith('.omex') or path.endswith('.sedx')):
                    omex_files.append(path)
    return omex_files


################################################
# Zip files
################################################
def zip_tree_content(path, entries=None):
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
            return '.'
        return '/'.join(tokens[:-1]) + '/'

    def find_name(filename):
        splited_file = filename.split("/")
        if splited_file[-1] == "":
            return splited_file[-2]
        return splited_file[-1]

    def node_from_filename(filename):
        icon = "fa fa-file-o fa-fw"
        if filename.endswith('/'):
            icon = "fa fa-folder fa-fw"

        node = {
            'id': filename,
            'parent': find_parent(filename),
            'text': find_name(filename),
            'icon': icon,
            'state': {'opened': True}
        }
        return node

    # Add the root node
    nodes = {}
    nodes['.'] = {
        'id': '.',
        'parent': "#",
        'text': '.',
        'icon': 'fa fa-fw fa-archive',
        'state': {'opened': True, 'selected': True}
    }

    with zipfile.ZipFile(path) as zip:
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

    # add entry information
    if entries:
        for entry in entries:

            # find node by location
            node_id = entry.location
            if node_id.startswith('./'):
                node_id = node_id[2:]
            elif node_id.startswith('.'):
                node_id = node_id[1:]
            if len(node_id) == 0:
                node_id = "."

            node = nodes.get(node_id)

            # add entry information
            if node:
                node['pk'] = entry.id
                node['format'] = entry.format
                node['master'] = entry.master
                node['location'] = entry.location
            else:
                raise ValueError("All entries must be part of the zip file.")

    tree_data = [nodes[key] for key in sorted(nodes.keys())]
    # pprint(tree_data)
    return json.dumps(tree_data)


################################################
# COMBINE archive
################################################
def entries_dict(archive_path):
    """ Parse entry information from given COMBINE archive.

    This is the main entry function to retrieve information from COMBINE archives.

    :param archive_path:
    :return:
    """
    # read combine archive contents & metadata
    omex = libcombine.CombineArchive()
    if omex.initializeFromArchive(archive_path) is None:
        print("Invalid Combine Archive: {}", archive_path)
        return None

    # metadata
    metadata_locations = []

    # add entries
    entries_dict = {}
    for i in range(omex.getNumEntries()):
        entry = omex.getEntry(i)
        location = entry.getLocation()
        format = entry.getFormat()

        entries_dict[location] = {
            'location': location,
            'format': format,
            'master': entry.getMaster(),
            'metadata': metadata_for_location(omex, location=location)
        }

        # collect metadata files in archive
        if format.endswith("omex-metadata"):
            metadata_locations.append(location)

    # add root information
    entries_dict['.'] = {
        'location': '.',
        'format': 'http://identifiers.org/combine.specifications/omex',
        'master': False,
        'metadata': metadata_for_location(omex, location=location)
    }

    omex.cleanUp()
    return entries_dict


def short_format(format):
    """ Returns short format string for given full format string.

    http://identifiers.org/combine.specifications/omex-metadata
    -> omex-metadata
    http://identifiers.org/combine.specifications/sbml.level-3.version-1
    -> sbml.level-3.version-1

    :param format: full format string
    :return: short format string
    """
    tokens = format.split("/")
    return tokens[-1]


def base_format(format):
    """ Returns the base format string for given full format string.

    http://identifiers.org/combine.specifications/omex-metadata
    -> omex-metadata
    http://identifiers.org/combine.specifications/sbml.level-3.version-1
    -> sbml

    :param format: full format string
    :return: base format string
    """
    tokens = format.split("/")
    short = tokens[-1].split('.')[0]
    short = short.replace('+xml', '')
    return short


# DEPRECATED, WILL BE REMOVED
# def omex():
#     """ Open CombineArchive for given archive.
#
#     Don't forget to close the omex after using it.
#     :return:
#     """
#     omex = libcombine.CombineArchive()
#     if omex.initializeFromArchive(self.path) is None:
#         logger.error("Invalid Combine Archive: {}", self)
#         return None
#     return omex
#
#
# def extract_entry_by_location(self, location, filename):
#     """ Extracts entry at location to filename.
#
#     :param location:
#     :param filename:
#     :return:
#     """
#     omex = self.omex()
#     entry = omex.getEntryByLocation(location)
#     omex.extractEntry(location, filename)
#     omex.cleanUp()
#
# def entry_content_by_index(self, index):
#     """ Extracts entry content at given index.
#
#     :param index: index of entry
#     :return: content
#     """
#     omex = self.omex()
#     entry = omex.getEntry(index)
#     content = omex.extractEntryToString(entry.getLocation())
#     omex.cleanUp()
#     return content
#
#
# def entry_content_by_location(self, location):
#     """ Extracts entry content at given location.
#
#     :param location: location of entry
#     :return: content
#     """
#     omex = self.omex()
#     entry = omex.getEntryByLocation(location)
#     content = omex.extractEntryToString(entry.getLocation())
#     omex.cleanUp()
#     return content
