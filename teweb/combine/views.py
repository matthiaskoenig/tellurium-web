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
    colors = [u'r', u'b', u'g', u'm', u'c', u'y', u'k'],
    facecolor = 'w',
    edgecolor = 'k',
    linewidth = 1.5,
    markersize = 3.0,

    output_id = output.getId()
    output_name = output.getName()

    title = output.getId()
    if output.isSetName():
        title = output.getName()

    js = "console.log('{}')\n".format(output_id)

    oneXLabel = True
    allXLabel = None
    curve_ids = []
    for kc, curve in enumerate(output.getListOfCurves()):
        curve_id = curve.getId()
        curve_ids.append(curve_id)
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

        # get x,y data for curve

        # create the traces
        x = dgs_dict[xId]
        y = dgs_dict[yId]
        x = [item for sublist in x for item in sublist]  # flatten
        y = [item for sublist in y for item in sublist]  # flatten
        js += """
            var {} = {{
                x: {},
                y: {},
                mode: 'lines+markers',
                name: 'Scatter + Lines'
            }};\n
            """.format(curve_id, x, y)

        # TODO: color, linewidth, markersize, alpha, label

        # TODO: handle the log
        '''
        if logX is True:
            lines.append("plt.xscale('log')")
        if logY is True:
            lines.append("plt.yscale('log')")
        '''

    # register traces
    js += "var data = {};\n".format(curve_ids)

    # register layout
    js += """
    var layout = {{
        title: '{}',
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
    return None


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


def get_commit():
    """ Get the current commit of the repository.
    Only works in the context of a git repository.
    Careful it returns the value of the current folder.
    Returns None if the commit cannot be resolved.
    :return:
    """
    import subprocess
    try:
        commit = subprocess.check_output(["git", "describe", "--always"])
        commit = commit.strip()
        return commit
    except Exception:
        return None

def about(request):
    """ About page. """
    commit = get_commit()
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


