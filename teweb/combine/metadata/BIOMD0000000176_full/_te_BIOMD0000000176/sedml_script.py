# -*- coding: utf-8 -*-
"""
Use Biomodels in phrasedml.

Example is the introduction example for the SED-ML specification.
Model is repressilator.
"""

from __future__ import absolute_import, print_function
import os
import tempfile
import shutil

import tellurium as te
from tellurium import temiriam
from tellurium.sedml.tesedml import executeCombineArchive, executeSEDML
from tellurium.utils import omex
import phrasedml

try:
    import libsbml
except ImportError:
    import tesbml as libsbml

r = te.loads("BIOMD0000000176.xml")
sbml_str = r.getCurrentSBML()
return_code = phrasedml.setReferencedSBML("./BIOMD0000000176.xml", sbml_str)
print('valid SBML', return_code)


phrasedml_str = """
    model1 = model "./BIOMD0000000176.xml"
    
    # sim1 = simulate uniform(0, 100, 100)
    sim1 = simulate steadystate
    task1 = run sim1 on model1
    task2 = repeat task1 for WGD_E in uniform(0.65, 1.0, 10), reset = true
    plot "Vmax decrease glycolysis" task2.WGD_E vs task2.GLCi, task2.NAD, task2.PYR
    plot "Vmax decrease glycolysis" task2.WGD_E vs task2.PYK
"""

# convert to sedml
sedml_str = phrasedml.convertString(phrasedml_str)
if sedml_str is None:
    print(phrasedml.getLastError())
    raise IOError("sedml could not be generated")
print(sedml_str)

with open("./simulation_new.xml", "w") as f_sedml:
    f_sedml.write(sedml_str)

