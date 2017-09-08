from django.conf.urls import url

from . import views

app_name = 'combine'
urlpatterns = [
    # ex: /combine/
    url(r'^$', views.archives, name='index'),
    # ex: /combine/5/
    url(r'^(?P<archive_id>[0-9]+)/$', views.archive_view, name='archive'),
    # ex: /combine/5/task
    url(r'^(?P<archive_id>[0-9]+)/task$', views.archive_task, name='archive_task'),

    # ex: /combine/upload
    url(r'^upload$', views.upload, name='upload'),

    # ex: /combine/upload
    url(r'^runall$', views.runall, name='runall'),
    #
    url(r'^taskresults$', views.taskresults, name='taskresults'),
    url(r'^taskresults/(?P<taskresult_id>[0-9]+)/$', views.taskresult, name='taskresult'),


    # /combine/5/check_state
    url(r'^(?P<archive_id>[0-9]+)/check_state$', views.check_state, name='check_state'),
    # /combine/5/aeeae648-25ec-49f2-a7ef-4285ad960276
    url(r'^(?P<archive_id>[0-9]+)/results$', views.results, name='results'),

    # ex: /combine/about
    url(r'^about$', views.about, name='about'),
]
