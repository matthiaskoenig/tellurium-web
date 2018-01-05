
import os
import tellurium
import matplotlib
from tellurium.sedml.tesedml import executeCombineArchive

matplotlib.use('Agg')
tellurium.setDefaultPlottingEngine("matplotlib")

input_path = "./BIOMD0000000176.omex"

filename, extension = os.path.splitext(os.path.basename(input_path))
workingDir = os.path.join(".", '_te_{}'.format(filename))
if not os.path.exists(workingDir):
    os.makedirs(workingDir)

executeCombineArchive(input_path, workingDir=workingDir, outputDir=workingDir, saveOutputs=True)