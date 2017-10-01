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
from celery import shared_task, task


# --------------------------------------------------
# Celery Tasks
# --------------------------------------------------


@task(name="execute omex")
def execute_omex(archive_id, debug=False):
    """
    Execute omex.
    """
    matplotlib.pyplot.switch_backend("Agg")

    print("*** START RUNNING OMEX ***")
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

    finally:
        # cleanup
        shutil.rmtree(tmp_dir)

    print("*** FINISHED RUNNING OMEX ***")
    return results

