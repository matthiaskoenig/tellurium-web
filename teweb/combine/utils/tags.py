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
        info.extend(_create_tags_sbml(entry))
    if format_id in ['sedml', 'sed-ml']:
        info.extend(_create_tags_sedml(entry))

    return info


def _create_tags_sbml(entry):
    """ Additional SBML tags.

    :param entry:
    :return:
    """
    info = []

    return info


def _create_tags_sedml(entry):
    """ Additional SED-ML tags.

    :param entry:
    :return:
    """
    info = []
    doc = libsedml.readSedMLFromFile(entry.path)  # type: libsedml.SedDocument

    for model in doc.getListOfModels():
        language = model.getLanguage()
        if language:
            name = language.split(':')[-1]
            info.append(
                TagInfo(category='sedml', name='model:{}'.format(name))
            )

    if len(doc.getListOfDataDescriptions()) > 0:
        info.append(
            TagInfo(category='sedml', name='DataDescription')
        )
    return info
