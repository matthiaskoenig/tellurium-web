"""
Helpers for working with the tree.
"""
import json
from pprint import pprint

# formats for which icon is shown in the UI
ICON_FORMATS = ['cellml', 'sed-ml', 'sbml', 'numl', 'csv', 'sbgn', 'omex', 'omex-manifest', 'omex-metadata']


def json_tree(archive):
    """ Returns the json tree structure for a given archive.

    The JSON data is in the following format (jstree)
        tree_data = [
            {"id": "ajson1", "parent": "#", "text": "Simple root node", "state": {"opened": True, "selected": True}},
            {"id": "ajson2", "parent": "#", "text": "Root node 2", "state": {"opened": True}},
            {"id": "ajson3", "parent": "ajson2", "text": "Child 1"},
            {"id": "ajson4", "parent": "ajson2", "text": "Child 2", "icon": "fa fa-play"}
        ]
    :param archive: Archive model object
    :return:
    """
    nodes = {}

    # Add root node
    nodes['.'] = {
        'id': '.',
        'parent': "#",
        'text': '.',
        'state': {'opened': True, 'selected': True}
    }

    # entry nodes
    directories = set()
    for entry in archive.entries.all():
        location = entry.location
        if location != ".":
            filename = location.replace("./", "")
            directories.update(directories_from_filename(filename))
            node = node_from_filename(filename)
        else:
            node = nodes['.']

        # add entry information
        node['pk'] = entry.id
        node['format'] = entry.format
        node['master'] = entry.master
        node['location'] = entry.location
        node['type'] = entry.base_format

        if entry.base_format in ICON_FORMATS:
            node["icon"] = '/static/combine/images/mediatype/thumbnails/{}.png'.format(entry.base_format)

        # store entry node
        nodes[node['id']] = node

    # directory nodes
    for filename in directories:
        node = node_from_filename(filename)
        nodes[node['id']] = node

    tree_data = [nodes[key] for key in sorted(nodes.keys())]
    # pprint(tree_data)
    return json.dumps(tree_data)

def node_from_filename(filename):
    icon = "far fa-file fa-fw fa-xs"
    if filename.endswith('/'):
        icon = "fa fa-folder fa-fw fa-xs"

    node = {
        'id': filename,
        'parent': find_parent(filename),
        'text': find_name(filename),
        'icon': icon,
        'state': {'opened': True}
    }
    return node


def find_parent(location):
    if location.endswith('/'):
        location = location[:-1]
    tokens = location.split("/")
    if len(tokens) == 1:
        return '.'
    return '/'.join(tokens[:-1]) + '/'


def find_name(filename):
    splited_file = filename.split("/")
    if splited_file[-1] == "":
        return splited_file[-2]
    return splited_file[-1]


def directories_from_filename(filename):
    """ All parent directories from filename for tree.

    :param filename:
    :return:
    """
    tokens = filename.split('/')
    dirs = set()
    directory = None
    for k, token in enumerate(tokens[:-1]):
        if k == 0:
            directory = token
        else:
            directory = directory + '/' + token
        dirs.add(directory + '/')
    return dirs
