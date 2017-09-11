"""
Tellurium SED-ML Tools Views

Creates the HTML views of the web-interface.
"""

from __future__ import print_function, absolute_import
from django.shortcuts import render, get_object_or_404, render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import RequestContext
from django_celery_results.models import TaskResult
from django.contrib.auth.decorators import login_required

from six import iteritems

from celery.result import AsyncResult
from .tasks import add, execute_omex

from .models import Archive, hash_for_file
from .forms import UploadArchiveForm
from .git import get_commit

import pandas
import numpy as np

import tellurium
import libsedml
from libsedml import SedOutput
import libcombine
import importlib
importlib.reload(libcombine)



######################
# ABOUT
######################
def about(request):
    """ About page. """
    context = {
        'commit': get_commit()
    }
    return render(request, 'combine/about.html', context)

@login_required
def runall(request):
    """ Runs all archives.

    :param request:
    :return:
    """
    all_archives = Archive.objects.all().order_by('-created')
    for archive in all_archives:
        # add.delay(4, 4)
        print('* creating new task')
        result = execute_omex.delay(archive_id=archive.id)
        archive.task_id = result.task_id
        archive.save()
    return redirect('combine:index')


######################
# ARCHIVES
######################
def archives(request, form=None):
    """ Overview of archives.

    :param request:
    :return:
    """
    archives = Archive.objects.all().order_by('-created')
    tasks = []
    for archive in archives:
        task = None
        if archive.task_id:
            task = AsyncResult(archive.task_id)
        tasks.append(task)

    if form is None:
        form = UploadArchiveForm()
    context = {
        'archives': archives,
        'tasks': tasks,
        'form': form
    }
    return render(request, 'combine/archives.html', context)


# FIXME: unify the results and archive view

def archive_view(request, archive_id):
    """ Single archive view.
    Displays the content of the archive.

    :param request:
    :param archive_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)
    omex, entries = archive.get_entries()

    # already task id assigned
    task = None
    task_result = None
    if archive.task_id:
        task = AsyncResult(archive.task_id)
        task_result = TaskResult.objects.filter(task_id=archive.task_id)
        if task_result and len(task_result)>0:
            print(task_result)
            task_result = task_result[0]

    # view context
    context = {
        'archive': archive,
        'omex': omex,
        'entries': entries,
        'task': task,
        'task_result': task_result,
    }

    return render(request, 'combine/archive.html', context)


def results(request, archive_id):
    """ View is called when results are ready.

    :param request:
    :param archive_id:
    :param task_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)
    omex, entries = archive.get_entries()

    # no task for the archive, so no results
    if not archive.task_id:
        return archive_view(request, archive_id)

    # Create the plots with the given results
    # The outputs are needed from sedml document
    task = AsyncResult(archive.task_id)
    task_result = TaskResult.objects.filter(task_id=archive.task_id)

    path = str(archive.file.path)
    omex = tellurium.tecombine.OpenCombine(path)


    outputs = []

    dgs_json = task.result["dgs"]
    for sedmlFile, dgs_dict in iteritems(dgs_json):

        # python 3
        sedmlStr = omex.getSEDML(sedmlFile).decode('UTF-8')
        doc = libsedml.readSedMLFromString(str(sedmlStr))

        # check that valid
        sedml_str = libsedml.writeSedMLToString(doc)

        # Stores all the html & js information for the outputs
        # necessary to handle the JS separately
        reports = []
        plot2Ds = []
        plot3Ds = []

        for output in doc.getListOfOutputs():
            outputs.append(output)

            # check what kind of output
            typeCode = output.getTypeCode()
            info = {}
            info["id"] = output.getId()
            info["name"] = output.getName()
            info["typeCode"] = typeCode

            if typeCode == libsedml.SEDML_OUTPUT_REPORT:
                df = create_report(doc, output, dgs_dict)
                html = df.to_html()
                html = html.replace('<table border="1" class="dataframe">', '<table class="table table-striped table-condensed table-hover">')
                info["html"] = html
                reports.append(info)

            elif typeCode == libsedml.SEDML_OUTPUT_PLOT2D:
                plot2D = create_plot2D(doc, output, dgs_dict)
                info["js"] = plot2D
                plot2Ds.append(info)

            elif typeCode == libsedml.SEDML_OUTPUT_PLOT3D:
                plot3D = create_plot3D(doc, output, dgs_dict)
                info["js"] = plot3D
                plot3Ds.append(info)

            else:
                print("# Unsupported output type: {}".format(output.getElementName()))

        # process all the outputs and create the respective graphs
        # TODO
        # for doc.getOutputs()
        # dgs

        # FIXME: Only processes the first file, than breaks
        break

    # provide the info to the view
    context = {
        'archive': archive,
        'entries': entries,
        'omex': omex,
        'task': task,
        'task_result': task_result,

        'doc': doc,
        'outputs': outputs,
        'reports': reports,
        'plot2Ds': plot2Ds,
        'plot3Ds': plot3Ds,
    }

    return render(request, 'combine/results.html', context)


def run_archive(request, archive_id):
    """ Executes the given archive.

    :param request:
    :param archive_id:
    :return:
    """
    create_task = False

    archive = get_object_or_404(Archive, pk=archive_id)
    if archive.task_id:
        result = AsyncResult(archive.task_id)
        # Create new task and run again.
        if result.status in ["FAILURE", "SUCCESS"]:
            create_task = True

    else:
        # no execution yet
        create_task = True

    if create_task:
        # add.delay(4, 4)
        print('* creating new task')
        result = execute_omex.delay(archive_id=archive_id)
        archive.task_id = result.task_id
        archive.save()

    return redirect('combine:archive', archive_id)




def upload_view(request, form):
    context = {
        'form': form,
    }
    return render(request, 'combine/archive_upload.html', context)


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
            # FIXME: hash
            # new_archive.md5 = hash_for_file(name, hash_type='MD5')
            new_archive.md5 = 'None'
            new_archive.full_clean()
            new_archive.save()
            return archive_view(request, new_archive.id)
        else:
            print('Form is invalid')
    else:
        form = UploadArchiveForm()

    return upload_view(request, form)


######################
# TASK RESULTS
######################
@login_required
def taskresults(request):
    """ View the task results.

    :param request:
    :return:
    """
    taskresults = TaskResult.objects.all()
    context = {
        'taskresults': taskresults,
    }
    return render(request, 'combine/taskresults.html', context)


def taskresult(request, taskresult_id):
    """ Single taskresult view.

    :param request:
    :param taskresult_id:
    :return:
    """
    taskresult = get_object_or_404(TaskResult, pk=taskresult_id)
    archives = Archive.objects.filter(task_id=taskresult.task_id)

    context = {
        'taskresult': taskresult,
        'archives': archives,
    }

    return render(request, 'combine/taskresult.html', context)


######################
# ARCHIVE EXECUTION
######################

def check_state(request, archive_id):
    """ A view to report the progress of the archive to the user. """
    if request.is_ajax():
        if 'task_id' in request.POST.keys() and request.POST['task_id']:
            task_id = request.POST['task_id']
            task = AsyncResult(task_id)
            data = {
                'state': task.state,
            }
            if task.state == "SUCCESS":
                data['result'] = task.result
        else:
            data = {
                'state': 'No task_id in the request'
            }

    else:
        data = {
            'state': 'This is not an ajax request'
        }

    return JsonResponse(data)



######################
# OUTPUTS
######################
def create_report(sed_doc, output, dgs_dict):
    """ Create the report from output

    :param output:
    :param sed_doc:
    :return:
    """
    output_id = output.getId()

    headers = []
    dgIds = []
    columns = []
    for dataSet in output.getListOfDataSets():
        # these are the columns
        headers.append(dataSet.getLabel())
        # data generator (the id is the id of the data in python)
        dgId = dataSet.getDataReference()
        dgIds.append(dgId)

        # write data
        data = dgs_dict[dgId]
        data = [item for sublist in data for item in sublist]  # flatten list
        columns.append(data)

    # print('header:', headers)
    # print('columns:')
    df = pandas.DataFrame(np.column_stack(columns), columns=headers)
    print(df.head(5))

    # csv = df.to_csv()

    return df


def create_plot2D(sed_doc, output, dgs_dict):
    """ Creates the necessary javascript for plotly.

    :param sed_document:
    :param output:
    :return: javascript code
    """

    # General settings
    colors = [
          'rgba(1.0, 0, 0, 1)',  # r
          'rgba(0, 0, 1.0, 1)',  # b
          'rgba(0, 0.5, 0, 1)',  # g
          'rgba(0.75, 0, 0.75, 1)',  # m
          'rgba(0, 0.75, 0.75, 1)',  # c
          'rgba(0.75, 0.75, 0, 1)',  # y
          'rgba(0, 0, 0, 1)',  # k
          ]

    facecolor = 'w',
    edgecolor = 'k',
    linewidth = 1.5,
    markersize = 3.0,

    output_id = output.getId()
    output_name = output.getName()

    title = output.getId()
    if output.isSetName():
        title = output.getName()

    js = ""  # created javascript code

    oneXLabel = True
    allXLabel = None
    trace_ids = []
    for kc, curve in enumerate(output.getListOfCurves()):
        color = colors[kc % len(colors)]
        curve_id = curve.getId()
        logX = curve.getLogX()
        logY = curve.getLogY()
        xId = curve.getXDataReference()
        yId = curve.getYDataReference()
        dgx = sed_doc.getDataGenerator(xId)
        dgy = sed_doc.getDataGenerator(yId)
        # color = settings.colors[kc % len(settings.colors)]

        yLabel = yId
        if curve.isSetName():
            yLabel = curve.getName()
        elif dgy.isSetName():
            yLabel = dgy.getName()
        xLabel = xId
        if dgx.isSetName():
            xLabel = dgx.getName()

        # do all curves have the same xLabel
        if kc == 0:
            allXLabel = xLabel
        elif xLabel != allXLabel:
            oneXLabel = False

        # create the traces from curve data
        x = dgs_dict[xId]
        y = dgs_dict[yId]
        # TODO: create all the repeats from the data
        Nrepeats = len(x[0])
        for k in range(Nrepeats):
            trace_id = "{}_{}".format(curve_id, k)
            trace_ids.append(trace_id)

            x_tr = [sublist[k] for sublist in x]  # flatten
            y_tr = [sublist[k] for sublist in y]  # flatten
            print(y_tr[-1], type(y_tr[-1]))

            # FIXME: nan fix, this is simulation issue
            x_tr = [x if not np.isnan(x) else 0 for x in x_tr]
            y_tr = [y if not np.isnan(y) else 0 for y in y_tr]


            # one data point ('lines+markers')
            if len(x_tr) == 1:
                mode = "markers"
            else:
                mode = "lines"

            name = "{}[{}]".format(yLabel, k)


            js += """
    var {} = {{
        x: {},
        y: {},
        mode: '{}',
        name: '{}',
        marker: {{
            color: '{}'
        }}
    }};
                """.format(trace_id, x_tr, y_tr, mode,
                           name, color)

        # TODO: color, linewidth, markersize, alpha, label

        # TODO: handle the log
        '''
        if logX is True:
            lines.append("plt.xscale('log')")
        if logY is True:
            lines.append("plt.yscale('log')")
        '''

    # register traces
    data_ids = ", ".join(trace_ids)
    js += """
    var data = [{}];
    """.format(data_ids)

    # register layout
    # TODO: check the oneXLable
    js += """
    var layout = {{
        // title: '{}',
        xaxis: {{
            title: '{}'
        }},
        yaxis: {{
            title: '{}'
        }}
    }};
    Plotly.newPlot('{}_plotly', data, layout);
    """.format(title, xLabel, yLabel, output_id)

    return js


def create_plot3D(sed_doc, output, dgs_dict):
    """

    :param sed_doc:
    :param output:
    :return:
    """
    # TODO: analoque to the plot2D

    return None
