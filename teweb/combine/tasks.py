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


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)
