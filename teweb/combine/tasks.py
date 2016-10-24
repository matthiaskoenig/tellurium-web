"""
Celery example

run the server via:
celery -A tasks worker --loglevel=info

registered as app and worker can be started via
celery -A teweb worker -l info
test task scheduler
celery -A teweb beat -l info


To call our task you can use the delay() method.
This is a handy shortcut to the apply_async() method which gives greater control of the task execution (see Calling Tasks)

Calling a task returns an AsyncResult instance,
which can be used to check the state of the task,
wait for the task to finish or get its return value
(or if the task failed, the exception and traceback).

"""
from __future__ import absolute_import, print_function

import time
import zipfile
import tempfile

from django.shortcuts import get_object_or_404
from celery import shared_task, task
from jobtastic import JobtasticTask

from .models import Archive
import tellurium as te


# --------------------------------------------------
# Celery Tasks
# --------------------------------------------------
class ExecuteOMEX(JobtasticTask):
    """
    Execution of CombineArchives via celery workers.
    """
    # These are the Task kwargs that matter for caching purposes
    significant_kwargs = [
        ('archive_id', str),
    ]
    # How long should we give a task before assuming it has failed?
    herd_avoidance_timeout = 30  # Shouldn't take more than 300 seconds
    # How long we want to cache results with identical ``significant_kwargs``
    cache_duration = 5
    # Note: 0 means different things in different cache backends. RTFM for yours.
    memleak_threshold = 0.01  # Mb

    def calculate_result(self, archive_id, **kwargs):
        """
        Execute omex.
        """
        print("*** START OMEX ***")
        total_count = 10
        results = {}

        import matplotlib
        matplotlib.pyplot.switch_backend("Agg")

        # read archive
        archive = get_object_or_404(Archive, pk=archive_id)
        omexPath = str(archive.file.path)
        self.update_progress(2, total_count)

        '''
        for k in range(total_count):
            self.update_progress(k, total_count)
            time.sleep(2)
        '''
        # execute the archive
        tmp_dir = tempfile.mkdtemp()
        te.executeOMEX(omexPath, workingDir=tmp_dir)



        self.update_progress(8, total_count)

        # store results of execution for rendering

        # TODO: python code
        # TODO: results
        results['data'] = [1, 2, 3]
        results['plot'] = 'Hello world'

        import shutil
        shutil.rmtree(tmp_dir)

        print("*** END OMEX ***")
        return results

    def executeOMEX(self, omexPath):
        """
        # Archive
        if zipfile.is_zipfile(omexPath):

            # a directory is created in which the files are extracted
            if workingDir is None:
                extractDir = os.path.join(os.path.dirname(os.path.realpath(omexPath)), '_te_{}'.format(filename))
            else:
                extractDir = workingDir

            # extract the archive to working directory
            CombineArchive.extractArchive(omexPath, extractDir)
            # get SEDML files from archive
            sedmlFiles = CombineArchive.filePathsFromExtractedArchive(extractDir, filetype='sed-ml')

            if len(sedmlFiles) == 0:
                raise IOError("No SEDML files found in COMBINE archive: {}".format(omexPath))

            for sedmlFile in sedmlFiles:
                factory = SEDMLCodeFactory(sedmlFile, workingDir=os.path.dirname(sedmlFile))
                factory.executePython()
        else:
            raise IOError("File is not an OMEX Combine Archive in zip format: {}".format(omexPath))
        """
        pass

        # TODO: What is required for plotting?
        # For every SED-ML file return a list of data generators
        # Use the data generators to create the outputs

        # Necessary to create files to store with combine archive.



@shared_task
def add(x, y):
    return x + y
