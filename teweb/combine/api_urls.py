"""
Definition of REST API urls.
"""

from django.conf.urls import url, include

from rest_framework import routers, serializers, viewsets
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.views import get_swagger_view

from . import views as teweb_views

# schema_view = get_schema_view(title='Tellurium Web API')  # Django rest framework
schema_view = get_swagger_view(title='Tellurium Web API')  # Swagger

router = routers.DefaultRouter()
router.register(r'users', teweb_views.UserViewSet, base_name='user')
router.register(r'tags', teweb_views.TagViewSet, base_name='tag')
router.register(r'archives', teweb_views.ArchiveViewSet, base_name='archive')

app_name = 'combine'
urlpatterns = [
    url(r'^$', schema_view),
    ]
urlpatterns += router.urls
