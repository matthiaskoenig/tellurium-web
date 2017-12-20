"""
Helper functions to work with combine archives and zip files.

Getting information out of the files.
"""
import os
import json
import zipfile
import warnings
import tempfile
from pprint import pprint

import xml.etree.ElementTree as ET

try:
    import libcombine
except ImportError:
    import tecombine as libcombine


def get_archive_paths(archive_dirs):
    """ Returns list of given combine archive paths from given list of directories.

    This includes all archives in subdirectories.

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
        # 'icon': '/static/combine/images/mediatype/sbml.png',
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

def create_manifest(archive):
    """ Creates the manifest information for the given archive.

    :param archive:
    :return:
    """

    pass


def read_manifest_entries(archive_path):
    """ Reads the information from the manifest.

    :param path:
    :return:
    """
    # parse information from manifest
    entries_dict = _parse_manifest_entries(archive_path=archive_path)

    # parse information from zip entries
    zip_dict = _parse_zip_entries(archive_path=archive_path)

    for location, zip_entry in zip_dict.items():
        # add entries from zip
        if location not in entries_dict:
            entries_dict[location] = zip_entry

    # add root information
    if '.' not in entries_dict:
        entries_dict['.'] = {
            'location': '.',
            'format': 'http://identifiers.org/combine.specifications/omex',
            'master': False,
            'source': 'zip',
        }

    return entries_dict


def _parse_manifest_entries(archive_path):
    """ Parses the manifest information from given archive.

    :param archive_path:
    :return:
    """
    MANIFEST = "manifest.xml"

    entries_dict = {}
    with zipfile.ZipFile(archive_path) as z:
        try:
            # raise KeyError if no manifest.xml
            zipinfo = z.getinfo(MANIFEST)

            xml_str = z.read(MANIFEST)
            # print(xml_str.decode("utf-8"))

            omex_manifest = ET.fromstring(xml_str)
            for content in omex_manifest:
                location = _normalize_location(content.attrib.get('location'))

                master = content.attrib.get('master', False)
                if master in ["T", "true"]:
                    master = True
                elif master in ["F", "false"]:
                    master = False

                entries_dict[location] = {
                    'location': location,
                    'format': content.attrib.get('format'),
                    'master': master,
                    'source': 'manifest'
                }

        except KeyError:
            warnings.warn("No 'manifest.xml' in COMBINE archive: {}".format(archive_path))
            return entries_dict

    # pprint(entries_dict)
    return entries_dict


def _normalize_location(location):
    """ Ensure that all locations are relative paths.

    :param location:
    :return:
    """
    if location is None:
        return location

    if (len(location) > 1) and (not location.startswith(".")):
        location = "./{}".format(location)
    elif len(location) == 0:
        location = "."

    return location


def _parse_zip_entries(archive_path):
    """ Infers the entries from the zip archive. """

    entries_dict = {}

    with zipfile.ZipFile(archive_path) as z:
        for name in z.namelist():
            location = _normalize_location(name)

            # skip directories
            if name.endswith("/"):
                continue

            # guess the format
            suffix = location.split('/')[-1]
            tmp = tempfile.NamedTemporaryFile("wb", suffix=suffix)
            tmp.write(z.read(name))

            format = libcombine.KnownFormats.guessFormat(tmp.name)
            master = False
            if libcombine.KnownFormats.isFormat(formatKey="sed-ml", format=format):
                master = True

            entries_dict[location] = {
                'location': location,
                'format': format,
                'master': master,
                'source': 'zip',
            }

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


if __name__ == "__main__":
    # archive_path = "./testdata/rdf/CombineArchiveShowCase.omex"
    archive_path = "./testdata/rdf/Desktop.zip"
    entries_dict = read_manifest_entries(archive_path)

    pprint(entries_dict)
