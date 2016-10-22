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

import os.path
import tellurium as te
import tempfile

@task(name="execute_omex")
def execute_omex(archive_id):
    print("start executing omex")
    time.sleep(1)
    print("finished executing omex")

    archive = get_object_or_404(Archive, pk=archive_id)
    omexPath = str(archive.file.path)

    # execute the archive
    # TODO


    # TODO: better implementation of execution
    # Celery with redis
    omexDir = os.path.dirname(os.path.realpath(__file__))

    workingDir = os.path.join(omexDir, "_te_CombineArchiveShowCase")
    tmp_dir = tempfile.mkdtemp()


    print("*" * 80)
    print("RUN OMEX")
    print("*" * 80)
    # te.executeOMEX(omexPath, workingDir=tmp_dir)

    print("...")
    import shutil
    shutil.rmtree(tmp_dir)

    print("*" * 80)


@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)