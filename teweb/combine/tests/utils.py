import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OMEX_SHOWCASE_PATH = os.path.join(BASE_DIR, './testdata/archives/CombineArchiveShowCase.omex')
OMEX_L1V3_IKAPPAB_PATH = os.path.join(BASE_DIR, './testdata/archives/L1V3_ikappab.omex')


ARCHIVE_DIRS = [os.path.join(BASE_DIR, "../../../archives")]