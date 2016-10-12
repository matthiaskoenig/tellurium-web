from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext

from .models import Archive
from .forms import UploadArchiveForm
import combine_tools


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


def execute(request, archive_id):
    """ Run the given archive.

    :param request:
    :type request:
    :param archive_id:
    :type archive_id:
    :return:
    :rtype:
    """

    archive = get_object_or_404(Archive, pk=archive_id)
    path = str(archive.file.path)

    # execute the archive
    # TODO

    # provide the info to the view
    context = {
        'archive': archive,
    }
    return render(request, 'combine/results.html', context)


def archive(request, archive_id):
    """ Single archive view.

    :param request:
    :param archive_id:
    :return:
    """
    archive = get_object_or_404(Archive, pk=archive_id)

    # read the archive contents & metadata
    path = str(archive.file.path)

    entries = []

    import libcombine
    co_archive = libcombine.CombineArchive()
    if not co_archive.initializeFromArchive(str(path)):
        print("Invalid Combine Archive")
    else:
        print("Num Entries: {0}".format(co_archive.getNumEntries()))
        for i in range(co_archive.getNumEntries()):
            entries.append(co_archive.getEntry(i))

    # entries = combine_tools.getEntries(path)
    print(entries)
    # combine_tools.get_content(archive)

    # provide the info to the view
    context = {
        'archive': archive,
        'co_archive': co_archive,
        'entries': entries,
    }
    entry = entries[0]
    print(entry.getLocation())

    return render(request, 'combine/archive.html', context)


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
            # TODO: validate the archive with the libcombine functionality

            return index(request, form)

            # return HttpResponseRedirect(reverse('combine:index'))
        else:
            print('Form is invalid')
    else:
        form = UploadArchiveForm()

    return index(request, form)


