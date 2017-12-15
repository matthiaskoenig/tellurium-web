"""
Model serialization used in the django-rest-framework.
"""

from rest_framework import serializers
from .models import Tag, Archive, ArchiveEntry, MetaData, Creator, Date, Triple
from django.contrib.auth.models import User


class TagSerializer(serializers.ModelSerializer):
    """ Serializing all Tags. """
    class Meta:
        model = Tag
        fields = ['category', 'name', 'uuid']

class CreatorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Creator
        fields = ['first_name', 'last_name', 'organisation', 'email']


class DateSerializer(serializers.SlugRelatedField, serializers.ModelSerializer):

    class Meta:
        model = Date
        fields = ['date']


class TripleSerializer( serializers.ModelSerializer):

    class Meta:
        model = Triple
        fields = ['subject', 'predicate', 'object']



class MetaDataSerializer(serializers.HyperlinkedModelSerializer):
    creators = CreatorSerializer(many=True, )
    modified = DateSerializer(many=True, queryset=Date.objects.all(), slug_field="date")


    class Meta:
        model = MetaData
        fields = ['description', 'creators', 'created', 'modified']


class ArchiveSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializing all Archives. """
    tags = serializers.HyperlinkedRelatedField(many=True, view_name='api:tag-detail', queryset=Tag.objects.all(), lookup_field='uuid')
    user = serializers.HyperlinkedRelatedField(view_name='api:user-detail', read_only=True)
    entries = serializers.HyperlinkedRelatedField(many=True, view_name='api:archive-entry-detail', queryset=ArchiveEntry.objects.all())


    class Meta:
        model = Archive
        fields = ['name', 'file', 'created', 'md5', 'task_id', 'uuid', 'entries', 'user', 'tags']


class ArchiveEntrySerializer(serializers.HyperlinkedModelSerializer):
    archive = serializers.HyperlinkedRelatedField(view_name='api:archive-detail', queryset=Archive.objects.all(), lookup_field='uuid')
    metadata = MetaDataSerializer()




    class Meta:
        model = ArchiveEntry
        fields = ['archive', 'location', 'format', 'master', 'metadata']




class UserSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializing all Users. """
    url = serializers.HyperlinkedIdentityField(view_name='api:user-detail')

    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']


