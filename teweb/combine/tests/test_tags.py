"""
Testing tags
"""
from ..utils import tags
from .utils import OMEX_SHOWCASE_PATH, OMEX_L1V3_IKAPPAB_PATH

# setup django environment
from combine.utils import django_setup

from django.test import TestCase


class TagsTests(TestCase):

    def test_showcase(self):
        tags_info = tags.create_tags_for_archive(OMEX_SHOWCASE_PATH)
        assert tags_info is not None
        assert len(tags_info) > 0

    def test_ikappab(self):
        tags_info = tags.create_tags_for_archive(OMEX_L1V3_IKAPPAB_PATH)
        assert tags_info is not None
        assert len(tags_info) > 0