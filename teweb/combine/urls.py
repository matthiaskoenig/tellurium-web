from django.conf.urls import url

from . import views

app_name = 'combine'
urlpatterns = [
    # ex: /combine/
    url(r'^$', views.index_view, name='index'),
    # ex: /combine/5/
    url(r'^(?P<archive_id>[0-9]+)/$', views.archive, name='archive'),
    # ex: /combine/upload
    url(r'^upload$', views.upload, name='upload'),
    # /combine/5/check_state
    url(r'^(?P<archive_id>[0-9]+)/check_state$', views.check_state, name='check_state'),
    # /combine/5/aeeae648-25ec-49f2-a7ef-4285ad960276
    url(r'^(?P<archive_id>[0-9]+)/(?P<task_id>.+)$', views.results, name='results'),

    # ex: /combine/about
    url(r'^about$', views.about, name='about'),
]
