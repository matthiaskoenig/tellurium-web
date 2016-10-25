"""
Tellurium SED-ML Tools Views

Creates the HTML views of the web-interface.
"""

from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from tasks import ExecuteOMEX

from .models import Archive
from .forms import UploadArchiveForm

from celery.result import AsyncResult

# import libcombine
from tellurium import tecombine


def index(request, form=None):
    """ Overview of archives.

    :param request:
    :return:
    """
    archives = Archive.objects.all().order_by('-created')
    if form is None:
        form = UploadArchiveForm()
    context = {
        'archives': archives,
        'form': form
    }
    return render(request, 'combine/index.html', context)


def archive(request, archive_id):
    """ Single archive view.

    :param request:
    :param archive_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)

    # read the archive contents & metadata
    path = str(archive.file.path)

    omex = tecombine.OpenCombine(path)
    entries = omex.listContents()

    """
    entries = []
    co_archive = libcombine.CombineArchive()
    if not co_archive.initializeFromArchive(str(path)):
        print("Invalid Combine Archive")
    else:
        print("Num Entries: {0}".format(co_archive.getNumEntries()))
        for i in range(co_archive.getNumEntries()):
            entries.append(co_archive.getEntry(i))
    """

    # run the archive as celery task (asynchronous)
    # result = execute_omex.delay(archive_id)

    result = ExecuteOMEX.delay_or_fail(
        archive_id=archive_id
    )
    # print("Task:", result)




    # provide the info to the view
    context = RequestContext(request, {
        'archive': archive,
        'entries': entries,
        'task_id': result.task_id,
    })

    return render_to_response('combine/archive.html', context)


def results(request, archive_id, task_id):
    """ View is called when results are ready.

    :param request:
    :param archive_id:
    :param task_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)

    task = AsyncResult(task_id)
    data = {
        'result': task.result,
        'state': task.state,
    }

    # Now create the plots with the given results
    # The outputs are needed from sedml document

    path = str(archive.file.path)
    omex = tecombine.OpenCombine(path)
    entries = omex.listContents()

    from tellurium.sedml.tesedml import SEDMLTools

    outputs = []
    for sedmlFile, dgs in task.result.iteritems():

        print(sedmlFile)
        sedmlStr = omex.getSEDML(sedmlFile)
        doc = SEDMLTools.readSEDMLDocument(sedmlStr)

        # process all the outputs and create the respective graphs
        # TODO
        # for doc.getOutputs()
        # dgs

        # FIXME: Only processes the first file, than breaks
        break

    #experiment1.xml
    omexPath = str(archive.file.path)


    # open the archive and read the sedml document


    # results['dgs'] = dgs_json


    # provide the info to the view
    context = RequestContext(request, {
        'archive': archive,
        'task_id': task_id,
    })

    return render_to_response('combine/results.html', context)



def check_state(request, archive_id):
    """ A view to report the progress of the archive to the user. """
    if request.is_ajax():
        if 'task_id' in request.POST.keys() and request.POST['task_id']:
            task_id = request.POST['task_id']
            task = AsyncResult(task_id)
            data = {
                'result': task.result,
                'state': task.state,
            }
        else:
            data = {
                'state': 'No task_id in the request'
            }

    else:
        data = {
            'state': 'This is not an ajax request'
        }

    return JsonResponse(data)


def about(request):
    """ About page. """
    import subprocess
    commit = subprocess.check_output(["git", "describe", "--always"])
    commit = commit.strip()
    context = {
        'commit': commit
    }

    return render(request, 'combine/about.html', context)


def upload(request):
    """ Upload file view.

    :param request:
    :return:
    """
    if request.method == 'POST':
        form = UploadArchiveForm(request.POST, request.FILES)
        if form.is_valid():
            name = request.FILES['file']
            new_archive = Archive(name=name, file=request.FILES['file'])
            new_archive.full_clean()
            new_archive.save()

            return index(request, form)
        else:
            print('Form is invalid')
    else:
        form = UploadArchiveForm()

    return index(request, form)


