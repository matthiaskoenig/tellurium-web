from django.conf.urls import url, include

from . import views as teweb_views
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.views import get_swagger_view
#schema_view = get_schema_view(title='Tellurium API')
schema_view = get_swagger_view(title='Tellurium API')
from rest_framework import routers, serializers, viewsets


router = routers.DefaultRouter()
router.register(r'users', teweb_views.UserViewSet,base_name='user')
router.register(r'tags', teweb_views.TagViewSet,base_name='tag')
router.register(r'archives', teweb_views.ArchiveViewSet,base_name='archive')


urlpatterns = [
    url(r'^$', schema_view),
]
urlpatterns += router.urls