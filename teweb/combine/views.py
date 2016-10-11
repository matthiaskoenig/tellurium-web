from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse

from .models import Archive
from.forms import UploadArchiveForm


def index(request):
    """ Overview of archives.

    :param request:
    :return:
    """
    archives = Archive.objects.all()
    context = {
        'archives': archives,
    }
    return render(request, 'combine/index.html', context)


def archive(request, archive_id):
    """ Single archive view.

    :param request:
    :param archive_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)
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
            new_archive = Archive(name=form.name, file=request.FILES['file'])
            new_archive.save()
            return HttpResponseRedirect(reverse('combine.views.index'))
    else:
        form = UploadArchiveForm()
    return render(request, 'combine/upload.html', {'form': form})
