"""
Configures the jinja2 template engine used for rendering.
"""

from __future__ import absolute_import

from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse

from jinja2 import Environment


def environment(**options):
    """ Environment definition for jinja2. """

    def f_finalize(arg):
        """ Finalize hook to handle None arguments for template.

        :param arg:
        :return:
        """
        return arg if arg is not None else '-'

    options['trim_blocks'] = True
    options['lstrip_blocks'] = True
    options['finalize'] = f_finalize

    # not yet supported
    # options['bytecode_cache'] = True

    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
    })
    return env
