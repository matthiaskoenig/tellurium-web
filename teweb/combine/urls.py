from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /combine/
    url(r'^$', views.index, name='index'),
    # ex: /combine/5/
    url(r'^(?P<archive_id>[0-9]+)/$', views.archive, name='archive'),
]
