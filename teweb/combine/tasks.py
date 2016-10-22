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
from celery import shared_task, task
import time

import tellurium as te
import tempfile
from django.shortcuts import get_object_or_404
from .models import Archive

# --------------------------------------------------
# Celery Tasks
# --------------------------------------------------
@shared_task(name="execute_omex")
def execute_omex(archive_id):
    import matplotlib
    matplotlib.pyplot.switch_backend("Agg")


    print("*" * 20)
    print("START OMEX")
    print("*" * 20)

    # time.sleep(3)

    archive = get_object_or_404(Archive, pk=archive_id)
    omexPath = str(archive.file.path)

    # execute the archive
    tmp_dir = tempfile.mkdtemp()
    te.executeOMEX(omexPath, workingDir=tmp_dir)

    # store the results somewhere for the archive on the server

    import shutil
    shutil.rmtree(tmp_dir)

    print("*" * 20)
    print("END OMEX")
    print("*" * 20)


@shared_task
def add(x, y):
    return x + y

# --------------------------------------------------
# jobtastic
# --------------------------------------------------

from time import sleep
from jobtastic import JobtasticTask


class LotsOfDivisionTask(JobtasticTask):
    """
    Division is hard. Make Celery do it a bunch.
    """
    # These are the Task kwargs that matter for caching purposes
    significant_kwargs = [
        ('numerators', str),
        ('denominators', str),
    ]
    # How long should we give a task before assuming it has failed?
    herd_avoidance_timeout = 60  # Shouldn't take more than 60 seconds
    # How long we want to cache results with identical ``significant_kwargs``
    cache_duration = 0  # Cache these results forever. Math is pretty stable.
    # Note: 0 means different things in different cache backends. RTFM for yours.

    def calculate_result(self, numerators, denominators, **kwargs):
        """
        MATH!!!
        """
        results = []
        divisions_to_do = len(numerators)
        # Only actually update the progress in the backend every 10 operations
        update_frequency = 10
        for count, divisors in enumerate(zip(numerators, denominators)):
            numerator, denominator = divisors
            results.append(numerator / denominator)
            # Let's let everyone know how we're doing
            self.update_progress(
                count,
                divisions_to_do,
                update_frequency=update_frequency,
            )
            # Let's pretend that we're using the computers that landed us on the moon
            sleep(0.1)

        return results