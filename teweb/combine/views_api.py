"""
REST API views.
"""

import logging

import json

from django.contrib.auth.models import User
from django_filters import rest_framework as filters

from rest_framework import viewsets, status
from rest_framework.reverse import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
import rest_framework.filters as filters_rest

from .models import Archive, Tag, ArchiveEntry, Creator, Date
from .serializers import ArchiveSerializer, TagSerializer, UserSerializer, ArchiveEntrySerializer, DateSerializer, \
    CreatorSerializer, MetaDataSerializer

from .permissions import IsOwnerOrReadOnly, IsAdminUserOrReadOnly, IsOwnerOfArchiveEntryOrReadOnly, \
    IsOwnerOrGlobalOrAdminReadOnly


###################################
# REST API
###################################
# TODO: authentication, get queries allowed for everyone, all other queries for authenticated
# TODO: provide url for download of archives
# TODO: use tag names in REST API
# TODO: API versioning
# TODO: improved swagger documentation
# TODO: fixed ids

class ArchiveViewSet(viewsets.ModelViewSet):
    """ REST archives.

    lookup_field defines the url of the detailed view.
    permission_classes define which users is allowed to do what.
    """

    queryset = Archive.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = ArchiveSerializer
    lookup_field = 'uuid'
    filter_backends = (filters.DjangoFilterBackend, filters_rest.SearchFilter)
    filter_fields = ('name', 'task_id', 'tags', 'created')
    search_fields = ('name', 'tags__name', 'created')

    def perform_create(self, serializer):
        # automatically set the user on create
        serializer.save(user=self.request.user)

    def list(self, request):
        global_user = User.objects.get(username="global")

        if request.user.is_authenticated:
            queryset = Archive.objects.filter(user__in=[global_user, request.user])
        else:
            queryset = Archive.objects.filter(user=global_user)
        context = {
            'request': request,
        }
        serializer = ArchiveSerializer(queryset, many=True, context=context)
        return Response(serializer.data)


class ArchiveEntryViewSet(viewsets.ModelViewSet):
    """ REST archive entries.

        lookup_field defines the url of the detailed view.
        permission_classes define which users is allowed to do what.
        """
    queryset = ArchiveEntry.objects.all()
    permission_classes = (IsOwnerOfArchiveEntryOrReadOnly,)
    serializer_class = ArchiveEntrySerializer


class TagViewSet(viewsets.ModelViewSet):
    """ REST tags. """
    queryset = Tag.objects.all()
    permission_classes = (IsAdminUserOrReadOnly,)
    serializer_class = TagSerializer
    lookup_field = 'uuid'
    filter_backends = (filters.DjangoFilterBackend, filters_rest.SearchFilter)
    filter_fields = ('category', 'name')
    search_fields = ('category', 'name')


class UserViewSet(viewsets.ModelViewSet):
    """ REST users.
    A viewset for viewing and editing user instances.
    """
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)
    queryset = User.objects.all()
    filter_backends = (filters.DjangoFilterBackend, filters_rest.SearchFilter)
    filter_fields = ('is_staff', 'username')
    search_fields = ('is_staff', 'username', "email")


class ZipTreeView(APIView):
    queryset = Archive.objects.all()
    permission_classes = (IsOwnerOrGlobalOrAdminReadOnly,)

    def get(self, request, *args, **kwargs):
        archive_id = kwargs.get('archive_id')
        archive = self.get_object(request)
        parsed = archive.tree_json()
        parsed = json.loads(parsed)
        return Response(parsed)

    def get_object(self, request):
        archive = self.queryset.get(pk=self.kwargs.get('archive_id'))
        self.user = archive.user
        self.check_object_permissions(request, obj=archive)
        return archive
