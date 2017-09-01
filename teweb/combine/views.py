"""
Tellurium SED-ML Tools Views

Creates the HTML views of the web-interface.
"""

from __future__ import print_function, absolute_import
from django.shortcuts import render, get_object_or_404, render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import RequestContext

from celery.result import AsyncResult
from .tasks import add, execute_omex

from .models import Archive, hash_for_file
from .forms import UploadArchiveForm
from .git import get_commit


try:
    import libcombine
except ImportError:
    import tecombine as libcombine


######################
# ABOUT
######################
def about(request):
    """ About page. """
    context = {
        'commit': get_commit()
    }
    return render(request, 'combine/about.html', context)


######################
# ARCHIVES
######################
def archives(request, form=None):
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
    return render(request, 'combine/archives.html', context)


def archive_view(request, archive_id):
    """ Single archive view.
    Displays the content of the archive.

    :param request:
    :param archive_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)
    path = str(archive.file.path)

    # read combine archive contents & metadata
    omex = libcombine.CombineArchive()
    if omex.initializeFromArchive(path) is None:
        print("Invalid Combine Archive")
        return None

    entries = []
    for i in range(omex.getNumEntries()):
        entry = omex.getEntry(i)
        # entry.getLocation(), entry.getFormat()
        # printMetaDataFor(archive, entry.getLocation());
        entries.append(entry)

        # the entry could now be extracted via
        # archive.extractEntry(entry.getLocation(), <filename or folder>)

        # or used as string
        # content = archive.extractEntryToString(entry.getLocation());

    # omex.cleanUp()

    # view context
    context = {
        'archive': archive,
        'omex': omex,
        'entries': entries,
    }

    return render(request, 'combine/archive.html', context)


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
            return archive(request, new_archive.id)
        else:
            print('Form is invalid')
    else:
        form = UploadArchiveForm()

    return archives(request, form)


######################
# ARCHIVE EXECUTION
######################
def archive_task(request, archive_id):
    """ Execute the given archive and show the task.

    :param request:
    :param archive_id:
    :return:
    """
    create_task = False

    archive = get_object_or_404(Archive, pk=archive_id)
    if archive.task_id:
        # existing task
        result = AsyncResult(archive.task_id)
        if result.status == "FAILURE":
            create_task = True
    else:
        create_task = True

    if create_task:
        # add.delay(4, 4)
        print('* creating new task')
        result = execute_omex.delay(archive_id=archive_id)
        archive.task_id = result.task_id
        archive.save()

    return archive_view(request, archive_id)




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
    omex = libcombine.OpenCombine(path)
    entries = omex.listContents()

    from tellurium.sedml.tesedml import SEDMLTools

    outputs = []

    import libsedml
    dgs_json = task.result["dgs"]
    for sedmlFile, dgs_dict in dgs_json.iteritems():

        print(sedmlFile)
        sedmlStr = omex.getSEDML(sedmlFile)
        doc = libsedml.readSedMLFromString(sedmlStr)

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
    context = RequestContext(request, {
        'archive': archive,
        'task_id': task_id,
        'doc': doc,
        'outputs': outputs,
        'reports': reports,
        'plot2Ds': plot2Ds,
        'plot3Ds': plot3Ds,
    })

    return render_to_response('combine/results.html', context)


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
    from libsedml import SedOutput
    import pandas
    import numpy as np


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
                }};\n
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
    js += "var data = [{}];\n".format(data_ids)

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
