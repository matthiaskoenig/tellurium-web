from django.conf.urls import url, include

from . import views
from . import views_api
app_name = 'combine'
urlpatterns = [

    url(r'^$', views.archives, name='index'),
    url(r'^archive/(?P<archive_id>[0-9]+)/$', views.archive_view, name='archive'),
    url(r'^archive/(?P<archive_id>[0-9]+)/results$', views.results, name='results'),
    url(r'^archive/(?P<archive_id>[0-9]+)/run$', views.run_archive, name='run_archive'),
    url(r'^archive/(?P<archive_id>[0-9]+)/delete$', views.delete_archive, name='delete_archive'),
    url(r'^archive/(?P<archive_id>[0-9]+)/download_initial$', views.download_archive_initial, name='download_archive_initial'),
    url(r'^archive/(?P<archive_id>[0-9]+)/download$', views.download_archive, name='download_archive'),
    url(r'^archive/(?P<archive_id>[0-9]+)/copy$', views.copy_archive, name='copy_archive'),
    url(r'^archives/(?P<user_id>[0-9]+)/$', views.user_archives, name='user_archives'),

    url(r'^archive/(?P<archive_id>[0-9]+)/zip_tree$', views_api.ZipTreeView.as_view(), name='zip_data'),

    url(r'^entry/(?P<entry_id>[0-9]+)$', views.archive_entry, name='archive_entry'),
    # url(r'^(?P<archive_id>[0-9]+)/previous$', views.archive_previous, name='archive_previous'),
    # url(r'^(?P<archive_id>[0-9]+)/next$', views.archive_next, name='archive_next'),

    url(r'^upload$', views.upload, name='upload'),
    url(r'^runall$', views.runall, name='runall'),
    url(r'^resetall$', views.resetall, name='resetall'),
    url(r'^runall/(?P<status>[.]+)/$', views.runall, name='runall'),

    url(r'^tags/$', views.tags, name='tags'),
    url(r'^tags/(?P<tag_id>[0-9]+)/$', views.tag, name='tag'),

    url(r'^taskresults$', views.taskresults, name='taskresults'),
    url(r'^taskresults/(?P<taskresult_id>[0-9]+)/$', views.taskresult, name='taskresult'),

    url(r'^about$', views.about, name='about'),

]
