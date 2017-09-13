from django.conf.urls import url

from . import views

app_name = 'combine'
urlpatterns = [

    url(r'^$', views.archives, name='index'),
    url(r'^(?P<archive_id>[0-9]+)/$', views.archive_view, name='archive'),
    url(r'^(?P<archive_id>[0-9]+)/previous$', views.archive_previous, name='archive_previous'),
    url(r'^(?P<archive_id>[0-9]+)/next$', views.archive_next, name='archive_next'),
    url(r'^(?P<archive_id>[0-9]+)/results$', views.results, name='results'),
    url(r'^(?P<archive_id>[0-9]+)/run$', views.run_archive, name='run_archive'),

    url(r'^(?P<archive_id>[0-9]+)/(?P<entry_index>[0-9]+)$', views.archive_entry, name='archive_entry'),

    url(r'^upload$', views.upload, name='upload'),
    url(r'^runall$', views.runall, name='runall'),

    url(r'^taskresults$', views.taskresults, name='taskresults'),
    url(r'^taskresults/(?P<taskresult_id>[0-9]+)/$', views.taskresult, name='taskresult'),

    # ex: /combine/about
    url(r'^about$', views.about, name='about'),

    url(r'^test$', views.test_view, name='test_view'),

    # ajax check
    # /combine/5/check_state
    # url(r'^(?P<archive_id>[0-9]+)/check_state$', views.check_state, name='check_state'),
]
