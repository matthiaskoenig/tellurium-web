
"""
terminate called after throwing an instance of 'std::runtime_error'
  what():  Error loading zip file!
Aborted (core dumped)

This is now fixed in the latest version.

"""
import libcombine
from tellurium import tecombine


def validate_omex(path):
    """ Simple validation by trying to load. """
    omex = libcombine.CombineArchive()
    print("Init archive:")
    if not omex.initializeFromArchive(path):
        print("Invalid Combine Archive")


if __name__ == "__main__":
    path = "BIOMD0000000012.sedx.zip"
    validate_omex(path)
