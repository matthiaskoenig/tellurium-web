"""
Definition of REST API urls.
"""

from django.conf.urls import url, include

from rest_framework import routers, serializers, viewsets
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.views import get_swagger_view

from . import views_api

#schema_view = get_schema_view(title='Tellurium Web API')  # Django rest framework
schema_view = get_swagger_view(title='Tellurium Web API')  # Swagger

router = routers.DefaultRouter()
router.register(r'users', views_api.UserViewSet, base_name='user')
router.register(r'tags', views_api.TagViewSet, base_name='tag')
router.register(r'archives', views_api.ArchiveViewSet, base_name='archive')
router.register(r'archive-entries', views_api.ArchiveEntryViewSet, base_name='archive-entry')


app_name = 'combine'
urlpatterns = [
    url(r'^$', schema_view, name="api"),
    ]
urlpatterns += router.urls
