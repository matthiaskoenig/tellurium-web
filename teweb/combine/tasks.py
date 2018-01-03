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
from __future__ import absolute_import, unicode_literals, print_function
import tempfile
import shutil
import matplotlib
from tellurium.sedml import tesedml

from .models import Archive
from django_celery_results.models import TaskResult
from celery import shared_task, task

import time
import json
import logging

from teweb.celery import app
from .models import Job
from channels import Channel


log = logging.getLogger(__name__)

@task(name="execute omex")
def execute_omex(archive_id, reply_channel, debug=False):
    """
    Execute omex.
    """
    matplotlib.pyplot.switch_backend("Agg")
    results = {}

    # get archive, raises ObjectDoesNotExist
    archive = Archive.objects.get(pk=archive_id)
    omex_path = str(archive.file.path)

    # execute archive
    try:
        tmp_dir = tempfile.mkdtemp()

        # dictionary of files to data generators
        te_result = tesedml.executeCombineArchive(omex_path, workingDir=tmp_dir, createOutputs=False)

        # JSON serializable results (np.array to list)
        dgs_json = {}
        for f_tmp, result in te_result.items():
            sedml_location = f_tmp.replace(tmp_dir + "/", "")

            dgs = result['dataGenerators']
            # print(sedml_location)
            for key in dgs:
                dgs[key] = dgs[key].tolist()
                # print(key, ':', dgs[key])
            dgs_json[sedml_location] = dgs
        # print("-" * 80)

        # store results of execution for rendering
        results['dgs'] = dgs_json
        # results['code'] = te_result['code']


        # Send status update back to browser client
        if reply_channel is not None:
            Channel(reply_channel).send({
                "text": json.dumps({
                    "task_id": archive.task_id,
                    "task_status": "SUCCESS",
                    "archive_id": archive_id,
                })
            })
    except:
        # Send status update back to browser client
        if reply_channel is not None:
            Channel(reply_channel).send({
                "text": json.dumps({
                    "task_id": archive.task_id,
                    "task_status": "FAILURE",
                    "archive_id": archive_id,
                })
            })

    finally:
        # cleanup
        shutil.rmtree(tmp_dir)

    return results
