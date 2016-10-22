from django.conf.urls import url

from . import views

app_name = 'combine'
urlpatterns = [
    # ex: /combine/
    url(r'^$', views.index, name='index'),
    # ex: /combine/5/
    url(r'^(?P<archive_id>[0-9]+)/$', views.archive, name='archive'),
    # ex: /combine/upload
    url(r'^upload$', views.upload, name='upload'),
    # ex: /combine/5/results
    url(r'^(?P<archive_id>[0-9]+)/results$', views.execute, name='execute'),

    # /combine/check_state
    url(r'^(?P<archive_id>[0-9]+)/check_state$', views.check_state, name='check_state'),

    # ex: /combine/about
    url(r'^about$', views.about, name='about'),
]
