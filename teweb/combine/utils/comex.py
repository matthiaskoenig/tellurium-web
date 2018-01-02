"""
Helper functions to work with combine archives and zip files.

Getting information out of the files.
"""
import os
import io
import json
import zipfile
import warnings
import tempfile
import magic
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
# COMBINE archive
################################################

def create_manifest(archive, debug=False):
    """ Creates the manifest information for the given archive.

    <?xml version="1.0" encoding="UTF-8"?>
    <omexManifest xmlns="http://identifiers.org/combine.specifications/omex-manifest">
        <content location="." format="http://identifiers.org/combine.specifications/omex" />
        ...
    </omexManifest>


    :param archive:
    :return:
    """
    from xml.etree.ElementTree import Element, SubElement, Comment
    from xml.dom import minidom

    def prettify(element):
        """Return a pretty-printed XML string for the Element.
        """
        xml_str = ET.tostring(element, 'utf-8')
        reparsed = minidom.parseString(xml_str)
        return reparsed.toprettyxml(indent="  ")

    n_omexManifest = Element('omexManifest')
    n_omexManifest.set('xmlns', 'http://identifiers.org/combine.specifications/omex-manifest')
    for entry in archive.entries.order_by('location'):
        n_content = SubElement(n_omexManifest, 'content')
        n_content.set('location', entry.location)
        n_content.set('format', entry.format)
        if entry.master is True:
            n_content.set('master', "true")

    xml_str = prettify(n_omexManifest)
    if debug:
        print('-' * 80)
        print(xml_str)
        print('-' * 80)
    return xml_str


class EntryParser(object):
    """ Helper class to parse the entries from a COMBINE archive. """

    FORMAT_PREFIX = "http://purl.org/NET/mediatypes/"
    FORMAT_COMBINE_PREFIX = "http://identifiers.org/combine.specifications"

    @staticmethod
    def read_manifest_entries(archive_path):
        """ Reads the information from the manifest.

        :param path:
        :return:
        """
        # parse information from manifest
        entries_dict = EntryParser._parse_manifest_entries(archive_path=archive_path)

        # parse information from zip entries
        zip_dict = EntryParser._parse_zip_entries(archive_path=archive_path)

        for location, zip_entry in zip_dict.items():
            # add entries from zip
            if location not in entries_dict:
                entries_dict[location] = zip_entry
            else:
                # add missing format keys
                entry = entries_dict[location]
                if entry.get("format") is None:
                    entry["format"] = zip_entry["format"]

        # add root information
        if '.' not in entries_dict:
            entries_dict['.'] = {
                'location': '.',
                'format': 'http://identifiers.org/combine.specifications/omex',
                'master': False,
                'source': 'zip',
            }

        return entries_dict

    @staticmethod
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
                    location = EntryParser._normalize_location(content.attrib.get('location'))
                    master = EntryParser._normalize_master(content.attrib.get('master', False))
                    format = EntryParser._normalize_format(content.attrib.get('format'))

                    entries_dict[location] = {
                        'location': location,
                        'format': format,
                        'master': master,
                        'source': 'manifest'
                    }

            except KeyError:
                warnings.warn("No 'manifest.xml' in COMBINE archive: {}".format(archive_path))
                return entries_dict

        # pprint(entries_dict)
        return entries_dict

    @staticmethod
    def _parse_zip_entries(archive_path):
        """ Infers the entries from the zip archive. """

        entries_dict = {}

        with zipfile.ZipFile(archive_path) as z:
            for name in z.namelist():
                location = EntryParser._normalize_location(name)

                # skip directories
                if name.endswith("/"):
                    continue

                # guess the format
                suffix = location.split('/')[-1]
                tmp = tempfile.NamedTemporaryFile("wb", suffix=suffix)
                tmp.write(z.read(name))

                format = libcombine.KnownFormats.guessFormat(tmp.name)
                if format is None:
                    mime = magic.Magic(mime=True)
                    format = mime.from_file(tmp.name)

                format = EntryParser._normalize_format(format)

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

    @staticmethod
    def _normalize_location(location):
        """ Normalizes the location representation.
        For instance ensures that all locations are relative paths.

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

    @staticmethod
    def _normalize_format(format):
        """ Normalizes the format representation.

        format: format string or ''
        """
        if format is None:
            return format

        if len(format) == 0:
            # Everything failed in format detection, fallback.
            # The "octet-stream" subtype is used to indicate that a body contains arbitrary binary data.
            format = "application/octet-stream"

        if format:
            lookup = libcombine.KnownFormats.lookupFormat(format)
            if len(lookup) > 0:
                format = lookup
            else:
                if not format.startswith(EntryParser.FORMAT_PREFIX) and not format.startswith(EntryParser.FORMAT_COMBINE_PREFIX):
                    format = EntryParser.FORMAT_PREFIX + format

        return format

    @staticmethod
    def _normalize_master(master):
        """ Normalizes the master representation. """
        if master in ["T", "true"]:
            master = True
        elif master in ["F", "false"]:
            master = False
        return master


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
