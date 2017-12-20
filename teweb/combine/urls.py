from django.conf.urls import url, include

from . import views
app_name = 'combine'
urlpatterns = [

    url(r'^$', views.archives, name='index'),
    url(r'^(?P<archive_id>[0-9]+)/$', views.archive_view, name='archive'),
    url(r'^(?P<archive_id>[0-9]+)/previous$', views.archive_previous, name='archive_previous'),
    url(r'^(?P<archive_id>[0-9]+)/next$', views.archive_next, name='archive_next'),
    url(r'^(?P<archive_id>[0-9]+)/results$', views.results, name='results'),
    url(r'^(?P<archive_id>[0-9]+)/run$', views.run_archive, name='run_archive'),
    url(r'^(?P<archive_id>[0-9]+)/delete$', views.delete_archive, name='delete_archive'),
    url(r'^(?P<archive_id>[0-9]+)/download$', views.download_archive, name='download_archive'),
    url(r'^(?P<archive_id>[0-9]+)/zip_tree$', views.ZipTreeView.as_view(), name='zip_data'),

    url(r'^entry/(?P<entry_id>[0-9]+)$', views.archive_entry, name='archive_entry'),

    url(r'^upload$', views.upload, name='upload'),
    url(r'^runall$', views.runall, name='runall'),
    url(r'^runall/(?P<status>[.]+)/$', views.runall, name='runall'),

    url(r'^tags/$', views.tags, name='tags'),
    url(r'^tags/(?P<tag_id>[0-9]+)/$', views.tag, name='tag'),

    url(r'^taskresults$', views.taskresults, name='taskresults'),
    url(r'^taskresults/(?P<taskresult_id>[0-9]+)/$', views.taskresult, name='taskresult'),

    # ex: /combine/about
    url(r'^about$', views.about, name='about'),
    url(r'^webservices$', views.webservices, name='webservices'),

    url(r'^test$', views.test_view, name='test_view'),

    #url(r'^api/', include('combine.api_urls', namespace='api')),

    # ajax check
    # /combine/5/check_state
    # url(r'^(?P<archive_id>[0-9]+)/check_state$', views.check_state, name='check_state'),
]
