"""
Helper functions to work with combine archives and zip files.

Getting information out of the files.
"""
import json
import zipfile

try:
    import libcombine
except ImportError:
    import tecombine as libcombine

# FIXME: this is a bugfix for https://github.com/sbmlteam/libCombine/issues/15
import importlib
importlib.reload(libcombine)


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

    for i in range(omex.getNumEntries()):
        entry = omex.getEntry(i)
        format = entry.getFormat()
        location = entry.getLocation()
        format_id = base_format(format)

        if format_id in ['sbml', 'cellml', 'sed-ml', 'sbgn', 'sbol']:
            tags_info.append({
                'type': 'format',
                'name': format_id,
            })

    # add the SBML contents
    # add the SED-ML contents

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

    def node_from_filename(filename):
        node = {}
        node['id'] = filename
        node['parent'] = find_parent(filename)
        node['text'] = filename
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
    check_ids = list(nodes.keys())  # make a copy we can iterate over
    for nid in check_ids:
        node = nodes[nid]
        parent_id = node['parent']
        if parent_id not in nodes and parent_id != "#":
            parent_node = node_from_filename(parent_id)
            nodes[parent_id] = parent_node
            # print("Added missing folder node:", parent_id)

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

