"""
Setup of django environment.

Import this module to perform the setup

    from combine.utils import django_setup
"""
import os
import sys

FILE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
PROJECT_DIR = os.path.join(FILE_DIR, "../../teweb/")
sys.path.append(PROJECT_DIR)

# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teweb.settings")

# django setup
import django
django.setup()
