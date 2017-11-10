"""
Model serialization used in the django-rest-framework.
"""

from rest_framework import serializers
from .models import Tag, Archive
from django.contrib.auth.models import User


class TagSerializer(serializers.ModelSerializer):
    """ Serializing all Tags. """
    class Meta:
        model = Tag
        fields = ['category', 'name', 'uuid']


class ArchiveSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializing all Archives. """
    tags = serializers.HyperlinkedRelatedField(many=True, view_name='api:tag-detail', queryset=Tag.objects.all(), lookup_field='uuid')
    user = serializers.HyperlinkedRelatedField(view_name='api:user-detail', read_only=True)

    #tags = serializers.StringRelatedField(many=True)
    class Meta:
        model = Archive
        fields = ['name', 'file', 'created', 'md5', 'task_id', 'uuid', 'user', 'tags']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializing all Users. """
    url = serializers.HyperlinkedIdentityField(view_name='api:user-detail')

    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']
