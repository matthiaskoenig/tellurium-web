"""
Validator functions for models and forms
"""
import magic
from django.template.defaultfilters import filesizeformat
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError

import libcombine


def validate_omex(data):
    """ Validate that file is a combine archive.

    :param omex:
    :return:
    """
    validate_file = FileValidator(max_size=1000000 * 100,
                                  content_types=('application/zip',))
    validate_file(data)

    # check that the omex can be read with libcombine
    # FIXME: not checked if archive can be read, this is done on access
    # path = ?
    # omex = libcombine.CombineArchive()
    # if omex.initializeFromArchive(path) is None:
    #    raise ValidationError("Combine archive is not valid. Reading with libcombine failed.")
    # omex.cleanUp()


@deconstructible
class FileValidator(object):
    error_messages = {
        'max_size': ("Ensure this file size is not greater than %(max_size)s."
                     " Your file size is %(size)s."),
        'min_size': ("Ensure this file size is not less than %(min_size)s. "
                     "Your file size is %(size)s."),
        'content_type': "Files of type %(content_type)s are not supported.",
    }

    def __init__(self, max_size=None, min_size=None, content_types=()):
        self.max_size = max_size
        self.min_size = min_size
        self.content_types = content_types

    def __call__(self, data):
        if self.max_size is not None and data.size > self.max_size:
            params = {
                'max_size': filesizeformat(self.max_size),
                'size': filesizeformat(data.size),
            }
            raise ValidationError(self.error_messages['max_size'],
                                  'max_size', params)

        if self.min_size is not None and data.size < self.min_size:
            params = {
                'min_size': filesizeformat(self.mix_size),
                'size': filesizeformat(data.size)
            }
            raise ValidationError(self.error_messages['min_size'],
                                  'min_size', params)

        '''
        if self.content_types:
            content_type = magic.from_buffer(data.read(), mime=True)
            if content_type not in self.content_types:
                params = {'content_type': content_type}
                raise ValidationError(self.error_messages['content_type'],
                                      'content_type', params)
        '''

    def __eq__(self, other):
        return isinstance(other, FileValidator)
