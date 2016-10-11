"""
Helper functions to work with combine archives.
"""
from __future__ import print_function, division
from .models import Archive

import libcombine
import libsbml




def get_content(archive):
    path = archive.file.path
    print(path)
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
    print("Hello world")



if __name__ == "__main__":
    import django
    django.setup()
    archive = Archive.objects.get(pk=10)
    print(archive)
    get_content(archive)




