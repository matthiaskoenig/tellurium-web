"""
Views definition.
"""
import logging

import pandas
import numpy as np
import json
import os
import tempfile
import shutil

from django.core.files.base import ContentFile

from django.shortcuts import render, get_object_or_404, render_to_response, redirect
from django.http import HttpResponse, FileResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django_celery_results.models import TaskResult
from celery.result import AsyncResult

from .tasks import execute_omex
from .models import Archive, Tag, ArchiveEntry, Creator, Date
from .serializers import ArchiveSerializer, TagSerializer, UserSerializer, ArchiveEntrySerializer, DateSerializer, \
    CreatorSerializer, MetaDataSerializer
from .forms import UploadArchiveForm
from .utils import comex, git
from rules.contrib.views import permission_required, objectgetter

try:
    import libsedml
except ImportError:
    import tesedml as libsedml

logger = logging.getLogger(__name__)


######################
# ABOUT
######################
def about(request):
    """ About page. """
    context = {
        'commit': git.get_commit()
    }
    return render(request, 'combine/about.html', context)


######################
# ARCHIVES
######################

def archives(request, form=None):
    """ Overview of archives.

    :param request:
    :param form:
    :return:
    """
    if request.user.is_superuser:
        archives = Archive.objects.all().order_by('-created')
    else:
        accepted_user = [request.user]
        try:
            global_user = User.objects.get(username="global")
            accepted_user.append(global_user)
        except User.DoesNotExist:
            pass

        archives = [archive  for archive  in Archive.objects.all().order_by('-created') if archive.user in accepted_user]

    if form is None:
        form = UploadArchiveForm()
    context = {
        'archives': archives,
        'form': form
    }
    return render(request, 'combine/archives.html', context)


@permission_required('archive.view_archive', fn=objectgetter(Archive, 'archive_id'))
def archive_view(request, archive_id):
    """ Single archive view.
    Displays the content of the archive.

    :param request:
    :param archive_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)
    context = archive_context(archive)

    # Check if a POST via the UI, i.e., changes to the archive, not new upload
    if request.method == 'POST' and "data" in request.POST:

        # keep track of modifications
        modified_metadata = False  # something changed in metadata
        modified_entry = False     # something changed in entry, i.e., format, master, location

        data = request.POST["data"]
        entrydata_dict = json.loads(data)
        # print(json.dumps(entrydata_dict, indent=4, sort_keys=True))

        archive_entry = ArchiveEntry.objects.get(id=entrydata_dict["id"])

        if entrydata_dict["master"] == "true":
            entrydata_dict["master"] = True
        elif entrydata_dict["master"] == "false":
            entrydata_dict["master"] = False

        # TODO: validation
        archive_entry_serializer = ArchiveEntrySerializer()
        archive_entry_serializer.update(instance=archive_entry, validated_data=entrydata_dict)
        if bool(archive_entry.changes()):
            modified_entry = True
        archive_entry.save()

        data = {"description": entrydata_dict["description"]}
        meta_data_serializer = MetaDataSerializer()
        meta_data_serializer.update(instance=archive_entry.metadata, validated_data=data)

        if bool(archive_entry.metadata.changes()):
            # Checks if description changed
            modified_metadata = True

        print(archive_entry.metadata.changes())


        archive_entry.metadata.save()
        if "creators" in entrydata_dict:
            for creator in entrydata_dict["creators"]:

                # Delete creator
                if creator["delete"] not in ["false", ""]:
                    creator = Creator.objects.get(id=creator["delete"])
                    creator.delete()
                    modified_metadata = True

                elif creator["delete"] == "":
                    # tries to delete a creator, which was not even created
                    pass

                # Create new creator
                elif creator["id"] == "new":
                    del creator["id"]
                    serializer_creator = CreatorSerializer(data=creator)
                    if serializer_creator.is_valid():
                        creator = serializer_creator.create(validated_data=serializer_creator.validated_data)
                        archive_entry.metadata.creators.add(creator)
                        modified_metadata = True
                    else:
                        response = {"errors": serializer_creator.errors, "is_error": True}
                        return JsonResponse(response)
                # Update creator
                else:
                    serializer_creator = CreatorSerializer(data=creator)
                    if serializer_creator.is_valid():
                        creator = Creator.objects.get(id=creator["id"])
                        serializer_creator.save()
                        serializer_creator.update(instance=creator, validated_data=serializer_creator.validated_data)
                        if bool(creator.changes()):
                            # checks what changed on creator
                            print(creator.changes())
                            modified_metadata = True
                        creator.save()
                    else:
                        response = {"errors": serializer_creator.errors, "is_error": True}
                        return JsonResponse(response)

        # add modified timestamp
        if modified_metadata or modified_entry:
            archive_entry.add_modified()

        # update manifest if entry information changed
        if modified_entry:
            archive.update_manifest_entry()

        # update metadata file if metadata changed
        if modified_metadata:
            archive.update_metadata_entry()

        return JsonResponse({"is_error": False})

    return render(request, 'combine/archive.html', context)


def upload(request):
    """ Upload file view.

    :param request:
    :return:
    """
    if request.method == 'POST':
        form = UploadArchiveForm(request.POST, request.FILES)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            file_name =  cleaned_data['file'].name
            file_obj = cleaned_data['file']
            file_obj2 = ContentFile(file_obj.read())
            dirpath = tempfile.mkdtemp()
            file_path = os.path.join(dirpath, file_name)

            create_dic = {}
            if request.user.is_authenticated:
                create_dic["user"] = request.user

            with open(file_path, 'wb+') as destination:
                destination.write(file_obj2.read())

                new_archive = Archive.objects.create(file=file_obj, **create_dic)
            shutil.rmtree(dirpath)

            # Everything uploaded, now display the entry
            return redirect('combine:archive', archive_id=new_archive.id)
            # return archive_view(request, new_archive.id)

        else:
            logging.warning('Form is invalid')
    else:
        form = UploadArchiveForm()

    return upload_view(request, form)


def upload_view(request, form):
    context = {
        'form': form,
    }
    return render(request, 'combine/archive_upload.html', context)


def archive_context(archive):
    """ Context required to render archive_content. """

    task = None
    task_result = None
    if archive.task_id:
        task = AsyncResult(archive.task_id)
        task_result = TaskResult.objects.filter(task_id=archive.task_id)
        if task_result and len(task_result) > 0:
            task_result = task_result[0]

    context = {
        'Creator': Creator,
        'archive': archive,
        'task': task,
        'task_result': task_result,
    }
    return context


def download_archive_initial(request, archive_id):
    """ Download the originally uploaded archive.

    :param request:
    :param archive_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)
    filename = archive.file.name.split('/')[-1]

    response = HttpResponse(archive.file, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    return response


def download_archive(request, archive_id):
    """ Download the latest archive.

    The archive is created dynamically, i.e., everything is packed in a zip archive.
    Manifest and metadata files are created from database content.

    :param request:
    :param archive_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)
    filename = archive.file.name.split('/')[-1]
    s = archive.create_omex_bytes()

    # Grab ZIP file from in-memory, make response with correct content type
    response = HttpResponse(s.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    return response


@login_required
def delete_archive(request, archive_id):
    """ Delete archive.

    :param request:
    :param archive_id:
    :return:
    """

    # FIXME: make sure only the own archives can be deleted
    archive = get_object_or_404(Archive, pk=archive_id)
    archive.delete()

    return redirect('combine:index')

######################
# ARCHIVE ENTRY
######################
def archive_entry(request, entry_id):
    """ Display an Archive Entry.

    :param request:
    :param archive_id:
    :param entry_id:
    :return:
    """
    entry = get_object_or_404(ArchiveEntry, pk=entry_id)
    context = {
        'entry': entry
    }
    return render(request, 'combine/entry.html', context)

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
# TAGS
######################
def tags(request):
    """ View the tags.

    :param request:
    :return:
    """
    tags = Tag.objects.all()
    context = {
        'tags': tags,
    }
    return render(request, 'combine/tags.html', context)


def tag(request, tag_id):
    """ Single tag view.

    :param request:
    :param tag_id:
    :return:
    """
    tag = get_object_or_404(Tag, pk=tag_id)
    archives = tag.archives.all()
    tasks = []
    for archive in archives:
        task = None
        if archive.task_id:
            task = AsyncResult(archive.task_id)
        tasks.append(task)
    context = {
        'tag': tag,
        'archives': archives,
        'tasks': tasks,
    }
    return render(request, 'combine/tag.html', context)


############################################
# EXECUTE COMBINE ARCHIVES
############################################
@login_required
def runall(request, status=None):
    """ Executes all archives.

    :param request:
    :return:
    """
    all_archives = Archive.objects.all().order_by('-created')
    for archive in all_archives:
        result = execute_omex.delay(archive_id=archive.id, reply_channel=None)
        archive.task_id = result.task_id
        archive.save()
    return redirect('combine:index')

@login_required
def resetall(request):
    """ Resets all archives, i.e., removing task results.

    :param request:
    :return:
    """
    all_archives = Archive.objects.all().order_by('-created')
    for archive in all_archives:
        # remove old TaskResult and reset task_id
       archive.reset_task()

    return redirect('combine:index')


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
            # reset task (and remove old task result)
            archive.reset_task()
    else:
        # no execution yet
        create_task = True

    if create_task:
        # add.delay(4, 4)
        result = execute_omex.delay(archive_id=archive_id)
        archive.task_id = result.task_id
        archive.save()

    return redirect('combine:archive', archive_id)


def results(request, archive_id):
    """ View is called when results are ready.

    :param request:
    :param archive_id:
    :param task_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)
    if not archive.task_id:
        return redirect('combine:archive', archive_id)

    # archive context
    context = archive_context(archive)
    task = context['task']
    if task.status != "SUCCESS":
        return redirect('combine:archive', archive_id)

    # output context
    outputs = []

    dgs_json = task.result["dgs"]

    for sedml_path, dgs_dict in dgs_json.items():
        sedml_location = comex.EntryParser._normalize_location(sedml_path)

        print("SEDML location:", sedml_location)
        archive_entries = ArchiveEntry.objects.filter(archive=archive.pk, location=sedml_location)
        print(archive_entries)
        # sedml_str = archive.entry_content_by_location(sedml_location)
        # sed_doc = libsedml.readSedMLFromString(sedml_str)
        sed_doc = libsedml.readSedMLFromFile(archive_entries[0].path)

        # Store html and JSON to render results
        reports = []
        plot2Ds = []
        plot3Ds = []

        for output in sed_doc.getListOfOutputs():
            outputs.append(output)

            # check what kind of output
            typeCode = output.getTypeCode()
            info = {}
            info["id"] = output.getId()
            info["name"] = output.getName()
            info["typeCode"] = typeCode

            if typeCode == libsedml.SEDML_OUTPUT_REPORT:
                df = create_report(sed_doc, output, dgs_dict)
                html = df.to_html()
                html = html.replace('<table border="1" class="dataframe">',
                                    '<table class="table table-striped table-condensed table-hover">')
                info["html"] = html
                reports.append(info)

            elif typeCode == libsedml.SEDML_OUTPUT_PLOT2D:
                plot2D = create_plot2D(sed_doc, output, dgs_dict)
                info["js"] = plot2D
                plot2Ds.append(info)

            elif typeCode == libsedml.SEDML_OUTPUT_PLOT3D:
                plot3D = create_plot3D(sed_doc, output, dgs_dict)
                info["js"] = plot3D
                plot3Ds.append(info)

            else:
                logging.warning("# Unsupported output type: {}".format(output.getElementName()))

        # FIXME: Only processes the first file, than breaks
        break

    # no SED-ML files in archive
    if len(dgs_json) == 0:
        sed_doc = None
        reports = []
        plot2Ds = []
        plot3Ds = []

    # add results context
    context.update({
        'doc': sed_doc,
        'outputs': outputs,
        'reports': reports,
        'plot2Ds': plot2Ds,
        'plot3Ds': plot3Ds,
    })

    return render(request, 'combine/results.html', context)


def create_report(sed_doc, output, dgs_dict):
    """ Create the report from output.

    Creates a pandas DataFrame.

    :param output:
    :param sed_doc:
    :return:
    """
    dgIds = []
    headers = []
    columns = []
    for dataSet in output.getListOfDataSets():
        headers.append(dataSet.getLabel())

        # data generator (the id is the id of the data in python)
        dgId = dataSet.getDataReference()
        dgIds.append(dgId)

        # write data
        data = dgs_dict[dgId]
        data = [item for sublist in data for item in sublist]  # flatten list
        columns.append(data)

    return pandas.DataFrame(np.column_stack(columns), columns=headers)


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
        # print(x)
        # print(y)

        Nrepeats = len(x[0])
        for k in range(Nrepeats):
            trace_id = "{}_{}".format(curve_id, k)
            trace_ids.append(trace_id)

            x_tr = [sublist[k] for sublist in x]  # flatten
            y_tr = [sublist[k] for sublist in y]  # flatten

            # This should never happen, but fixes NaN issues
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
    # TODO: analogue to the plot2D

    return None


def check_state(request, archive_id):
    """ A view to report the progress of the archive to the user. """
    if request.is_ajax():
        if 'task_id' in request.POST.keys() and request.POST['task_id']:
            task_id = request.POST['task_id']
            task = AsyncResult(task_id)
            data = {
                'status': task.status
            }
        else:
            data = {
                'status': 'No task_id in the request'
            }
    else:
        data = {
            'status': 'This is not an ajax request'
        }

    return JsonResponse(data)


