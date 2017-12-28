"""
Functions to work with archive tags and calulate archive tags.
"""

from collections import namedtuple
from .comex import base_format

try:
    import libcombine
except ImportError:
    import tecombine as libcombine

try:
    import libsedml
except ImportError:
    import tesedml as libsedml


TagInfo = namedtuple("TagInfo", "category name")


def create_tags_for_entry(entry):
    """ Creates tag info for given entry.

    :param entry:
    :return:
    """
    info = []


    format_id = base_format(entry.format)
    if format_id in ['sbml', 'cellml', 'sed-ml', 'sedml', 'sbgn', 'sbol']:
        info.append(
            TagInfo(category='format', name=format_id)
        )
    if format_id == 'sbml':
        tags.extend(sbml_entries.append(entry)
    if format_id in ['sedml', 'sed-ml']:
        sedml_entries.append(entry)


def create_


def create_tags_for_archive(archive_path):
    """ Creates the tags information for a given archive_path.

    :param archive_path: path to archive.
    :return: list of TagInfo
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
