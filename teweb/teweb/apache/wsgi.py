"""
WSGI config for teweb project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""


import os
import sys
import django.core.handlers.wsgi


# Calculate the path based on the location of the WSGI script.
apache_configuration = os.path.dirname(__file__)
project = os.path.dirname(apache_configuration)
workspace = os.path.dirname(project)

sys.path.append(workspace)
sys.path.append(project)

# Add the path to 3rd party django application and to django itself.
sys.path.append('/home/myuser')

os.environ['DJANGO_SETTINGS_MODULE'] = 'teweb.apache.override'

application = django.core.handlers.wsgi.WSGIHandler()
