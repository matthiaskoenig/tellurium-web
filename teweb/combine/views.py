from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404

from .models import Archive


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


