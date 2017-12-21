"""
Tellurium SED-ML Tools Views

Creates the HTML views of the web-interface.
"""
import logging

import pandas
import numpy as np
import magic
import json
import rdflib
import os
import tempfile
import shutil

from django.utils import timezone
from django.core.files.base import ContentFile



from rest_framework.reverse import reverse
from django.shortcuts import render, get_object_or_404, render_to_response, redirect
from django.http import HttpResponse, FileResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.temp import NamedTemporaryFile
from django_celery_results.models import TaskResult
from celery.result import AsyncResult
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from combine import comex


from .tasks import execute_omex
from .models import Archive, Tag, ArchiveEntry, Creator, Date
from .serializers import ArchiveSerializer, TagSerializer, UserSerializer, ArchiveEntrySerializer,DateSerializer,CreatorSerializer, MetaDataSerializer

from .forms import UploadArchiveForm
from .git import get_commit
from rest_framework.generics import (ListCreateAPIView,RetrieveUpdateDestroyAPIView)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.request import Request

from .permissions import IsOwnerOrReadOnly, IsAdminUserOrReadOnly, IsOwnerOfArchiveEntryOrReadOnly, IsOwnerOrGlobalOrAdminReadOnly
from rest_framework import viewsets
from django_filters import rest_framework as filters
import rest_framework.filters as filters_rest


import tellurium

try:
    import libsedml
except ImportError:
    import tesedml as libsedml

try:
    import libcombine
except ImportError:
    import tecombine as libcombine

import importlib
importlib.reload(libcombine)


logger = logging.getLogger(__name__)


######################
# ABOUT
######################
@login_required
def test_view(request):
    """ Test page. """
    context = {}
    return render(request, 'combine/test.html', context)


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
    :param form:
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
    context = archive_context(archive)


    if request.method =='POST':

        modified = False
        data = request.POST["data"]
        entrydata_dict = json.loads(data)
        print(json.dumps(entrydata_dict, indent=4, sort_keys=True))


        archive_entry = ArchiveEntry.objects.get(id=entrydata_dict["id"])

        if entrydata_dict["master"]=="true":
            entrydata_dict["master"] = True
        elif entrydata_dict["master"]=="false":
            entrydata_dict["master"] = False

        #todo: valdidation
        archive_entry_serializer = ArchiveEntrySerializer()
        archive_entry_serializer.update(instance=archive_entry, validated_data=entrydata_dict )
        if bool(archive_entry.changes()):
            modified = True
        archive_entry.save()

        data={"description":entrydata_dict["description"]}
        meta_data_serializer = MetaDataSerializer()
        meta_data_serializer.update(instance = archive_entry.metadata, validated_data=data )
        if bool(archive_entry.metadata.changes()):
            modified = True
        archive_entry.metadata.save()


        for creator in entrydata_dict["creators"]:
            if "delete" in creator:
                creator = Creator.objects.get(id=creator["delete"])
                creator.delete()

            elif creator["id"]== "new":
                del creator["id"]
                serializer_creator = CreatorSerializer(data=creator)
                if serializer_creator.is_valid():
                    creator = serializer_creator.create(validated_data=serializer_creator.validated_data)
                    archive_entry.metadata.creators.add(creator)
                    modified = True
                else:
                    response = {"errors":serializer_creator.errors,"is_error":True}
                    return JsonResponse(response)
            else:
                serializer_creator = CreatorSerializer(data=creator)
                if serializer_creator.is_valid():
                    creator = Creator.objects.get(id = creator["id"])
                    serializer_creator.save()
                    serializer_creator.update(instance=creator,validated_data=serializer_creator.validated_data)
                    if bool(creator.changes()):
                        modified = True
                    creator.save()
                else:
                    response = {"errors":serializer_creator.errors,"is_error":True}
                    return JsonResponse(response)


        if modified:
            date = Date.objects.create(date=timezone.now())
            archive_entry.metadata.modified.add(date)

        return JsonResponse({"is_error": False})
















    return render(request, 'combine/archive.html', context)


def archive_context(archive):
    """ Context required to render archive_content"""
    # omex entries
    entries = archive.omex_entries()

    # task and taskresult
    task = None
    task_result = None
    if archive.task_id:
        task = AsyncResult(archive.task_id)
        task_result = TaskResult.objects.filter(task_id=archive.task_id)
        if task_result and len(task_result) > 0:
            task_result = task_result[0]

    context = {
        'archive': archive,
        'task': task,
        'task_result': task_result,
    }
    return context


def download_archive(request, archive_id):
    """ Download archive.

    :param request:
    :param archive_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)
    filename = archive.file.name.split('/')[-1]

    response = HttpResponse(archive.file, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    # no redirecting, but breaks on archives
    # url = reverse('combine:archive', args=(archive_id,))
    # response['Refresh'] = "0;url={}".format(url)

    return response


@login_required
def delete_archive(request, archive_id):
    """ Delete archive.

    :param request:
    :param archive_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)
    archive.delete()

    return redirect('combine:index')


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

            file_name = request.FILES['file'].name
            file_obj = request.FILES['file']
            file_obj2 = ContentFile(file_obj.read())
            dirpath = tempfile.mkdtemp()
            file_path = os.path.join(dirpath,file_name)

            create_dic = {}
            if request.user.is_authenticated:
                create_dic["user"] = request.user

            with open(file_path, 'wb+') as destination:
                destination.write(file_obj2.read())

                new_archive, _ = Archive.objects.get_or_create(archive_path=file_path, **create_dic)
            shutil.rmtree(dirpath)


            return archive_view(request, new_archive.id)
        else:
            logging.warning('Form is invalid')
    else:
        form = UploadArchiveForm()

    return upload_view(request, form)


def archive_next(request, archive_id):
    """ Returns single archive view of next archive.
    Displays the content of the archive.

    :param request:
    :param archive_id:
    :return:
    """
    return archive_adjacent(request, archive_id, order='pk')


def archive_previous(request, archive_id):
    """ Returns single archive view of previous archive.
    Displays the content of the archive.

    :param request:
    :param archive_id:
    :return:
    """
    return archive_adjacent(request, archive_id, order='-pk')


def archive_adjacent(request, archive_id, order):
    """ Returns adjacent archive view.

    :param request:
    :param archive_id:
    :param order: order parameter to decide adjacent
    :return:
    """
    if order.startswith("-"):
        adj_archive = Archive.objects.filter(pk__lt=archive_id).order_by(order)[0:1]
    else:
        adj_archive = Archive.objects.filter(pk__gt=archive_id).order_by(order)[0:1]
    if len(adj_archive) == 1:
        pk = adj_archive[0].pk
    else:
        pk = archive_id

    referer = request.META.get('HTTP_REFERER')
    if referer.endswith('results'):
        return redirect('combine:results', pk)
    else:
        return redirect('combine:archive', pk)


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
    # TODO: implement allow filtering by status


    all_archives = Archive.objects.all().order_by('-created')
    for archive in all_archives:
        result = execute_omex.delay(archive_id=archive.id)
        archive.task_id = result.task_id
        archive.save()
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
        sedml_location = comex._normalize_location(sedml_path)

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
                html = html.replace('<table border="1" class="dataframe">', '<table class="table table-striped table-condensed table-hover">')
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


###################################
# REST API
###################################
# TODO: authentication, get queries allowed for everyone, all other queries for authenticated
# TODO: provide url for download of archives
# TODO: use tag names in REST API
# TODO: API versioning
# TODO: improved swagger documentation
# TODO: fixed ids


def webservices(request):
    """ Web services page. """
    context = {

    }
    return render(request, 'combine/webservices.html', context)


class ArchiveViewSet(viewsets.ModelViewSet):
    """ REST archives.

    lookup_field defines the url of the detailed view.
    permission_classes define which users is allowed to do what.
    """

    queryset = Archive.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = ArchiveSerializer
    lookup_field = 'uuid'
    filter_backends = (filters.DjangoFilterBackend, filters_rest.SearchFilter)
    filter_fields = ('name', 'task_id', 'tags', 'created')
    search_fields = ('name', 'tags__name', 'created')

    def perform_create(self, serializer):
        # automatically set the user on create
        serializer.save(user=self.request.user)

    def list(self, request):
         global_user = User.objects.get(username="global")

         if request.user.is_authenticated:
            queryset = Archive.objects.filter(user__in=[global_user,request.user])
         else:
             queryset = Archive.objects.filter(user=global_user)
         serializer_context = {
             'request': Request(request),
         }
         serializer = ArchiveSerializer(queryset, many=True, context=serializer_context)
         return Response(serializer.data)


class ArchiveEntryViewSet(viewsets.ModelViewSet):
    """ REST archive entries.

        lookup_field defines the url of the detailed view.
        permission_classes define which users is allowed to do what.
        """
    queryset = ArchiveEntry.objects.all()
    permission_classes = (IsOwnerOfArchiveEntryOrReadOnly,)
    serializer_class = ArchiveEntrySerializer


class TagViewSet(viewsets.ModelViewSet):
    """ REST tags. """
    queryset = Tag.objects.all()
    permission_classes = (IsAdminUserOrReadOnly,)
    serializer_class = TagSerializer
    lookup_field = 'uuid'
    filter_backends = (filters.DjangoFilterBackend,filters_rest.SearchFilter)
    filter_fields = ('category', 'name')
    search_fields = ('category', 'name')


class UserViewSet(viewsets.ModelViewSet):
    """ REST users.
    A viewset for viewing and editing user instances.
    """
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)
    queryset = User.objects.all()
    filter_backends = (filters.DjangoFilterBackend, filters_rest.SearchFilter)
    filter_fields = ('is_staff', 'username')
    search_fields = ('is_staff', 'username', "email")



class ZipTreeView(APIView):
    queryset = Archive.objects.all()
    permission_classes = (IsOwnerOrGlobalOrAdminReadOnly,)


    def get(self, request,*args, **kwargs):
       
        archive_id = kwargs.get('archive_id')
        archive = self.get_object(request)
        parsed = archive.tree_json()
        parsed = json.loads(parsed)
        return Response(parsed)


    def get_object(self,request):
        archive = self.queryset.get(pk=self.kwargs.get('archive_id'))
        self.user =archive.user
        self.check_object_permissions(request,obj=archive)
        return archive




