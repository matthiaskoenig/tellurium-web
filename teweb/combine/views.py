from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from .models import Archive


def index(request):
    """ Overview of archives.

    :param request:
    :return:
    """
    archives = Archive.objects.all()
    template = loader.get_template('combine/index.html')
    context = {
        'archives': archives,
    }
    return HttpResponse(template.render(context, request))


def archive(request, archive_id):
    """ Single archive view.

    :param request:
    :param archive_id:
    :return:
    """
    return HttpResponse("You're looking at archive %s." % archive_id)
