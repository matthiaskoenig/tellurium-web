from __future__ import print_function, division
import libcombine
import os

def get_content(path):
    print(path)
    print('path exists:', os.path.exists(path))

    # libsbml.readSBMLFromFile(path)
    manifest = libcombine.readOMEXFromFile(str(path))

    print("Errors:", manifest.getNumErrors())
    for k in xrange(manifest.getNumErrors()):
        error = manifest.getError(k)
        print(error)
        print(error.getErrorId())
        print(error.getMessage())


    # make CaListOfContents iteratable
    contentsList = manifest.getListOfContents()
    print('Contents: ', contentsList.getNumContents())
    for k in xrange(contentsList.getNumContents()):
        cabase = contentsList.get(k)
        print(cabase)

    print(manifest)


if __name__ == "__main__":
    """
    Try to read the showcase archive.
    """
    archive = "CombineArchiveShowCase.omex"
    get_content(archive)
