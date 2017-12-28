"""
Utilities to work with HTML.

Template creation.
"""
import json
from django.utils import safestring
from html import unescape, escape



def input_template(**kwargs):
    input_string = ""
    for key, value in kwargs.items():
        if value is None:
            value = ""
        input_string += " " + key + "='" + value + "' "

    return unescape("<input"+input_string +"/>")


def html_creator(first_name, last_name, organisation, email):
    if first_name is None:
        first_name = ""
    if last_name is None:
        last_name = ""
    if organisation is None or len(organisation) == 0:
        organisation_str = ""
    else:
        organisation_str = "({})".format(organisation)
    if email is None:
        email_str = ""
    else:
        email_str = '<a href="mailto:{}" target="_blank" title="{}"><i class="fa fa-fw fa-envelope"></i></a>'.format(email, email)

    html = '<i class="fa fa-fw fa-user"></i> {} {} {} {}'.format(first_name, last_name, email_str, organisation_str)

    # html = '{}{} {} ({})'.format(first_name, last_name, email, organisation)
    return unescape(html)
    #return safestring.mark_safe(html)

