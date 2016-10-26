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

import tempfile

from django.shortcuts import get_object_or_404

from celery import shared_task, task
from jobtastic import JobtasticTask

from .models import Archive
import tellurium as te
import time


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
        self.update_progress(1, total_count)

        # read archive
        archive = get_object_or_404(Archive, pk=archive_id)
        omexPath = str(archive.file.path)
        self.update_progress(2, total_count)

        # execute archive
        tmp_dir = tempfile.mkdtemp()

        # TODO: execute without making images for speedup
        dgs_all = te.executeOMEX(omexPath, workingDir=tmp_dir)

        # print("dgs_all:", dgs_all)

        self.update_progress(6, total_count)

        # JSON serializable results (np.array to list)
        print("-" * 80)
        dgs_json = {}
        for f_tmp, dgs in dgs_all.iteritems():
            print(f_tmp)
            sedmlFile = f_tmp.replace(tmp_dir + "/", "")
            print(sedmlFile)
            for key in dgs:
                dgs[key] = dgs[key].tolist()
                print(key, ':', dgs[key])
            dgs_json[sedmlFile] = dgs
        print("-" * 80)
        self.update_progress(8, total_count)



        import shutil
        shutil.rmtree(tmp_dir)

        # store results of execution for rendering
        results['dgs'] = dgs_json

        print("*** END OMEX ***")
        return results
