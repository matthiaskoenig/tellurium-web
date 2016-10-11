from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext

from .models import Archive
from.forms import UploadArchiveForm


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

    # read the archive



    return render(request, 'combine/archive.html', {'archive': archive})


def about(request):
    """ About page. """
    return render(request, 'combine/about.html', {})


def upload(request):
    """ Upload file view.

    :param request:
    :return:
    """
    if request.method == 'POST':
        form = UploadArchiveForm(request.POST, request.FILES)
        if form.is_valid():
            print('Handling uploaded file')

            name = request.FILES['file']
            new_archive = Archive(name=name, file=request.FILES['file'])
            new_archive.save()

            # validate


            # TODO: validate the archive

            return index(request, form)

            # return HttpResponseRedirect(reverse('combine:index'))
        else:
            print('Form is invalid')
    else:
        form = UploadArchiveForm()

    return index(request, form)


