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
        fields = ['first_name', 'last_name', 'organisation', 'email','id']

    def get(self,validated_data):
        return Creator.objects.get(**validated_data)

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name",instance.first_name)
        instance.last_name = validated_data.get("last_name",instance.last_name)
        instance.organisation = validated_data.get("organisation",instance.organisation)
        instance.email = validated_data.get("email",instance.email)






class DateSerializer(serializers.ModelSerializer):

    def get(self,validated_data):
        return Date.objects.get(**validated_data)

    def update(self, instance, validated_data):
        instance.date = validated_data.get("date",instance.date)
        return instance

    def create(self, validated_data):
        return Date.objects.create(**validated_data)

    class Meta:
        model = Date
        fields = ['date','id']


class TripleSerializer( serializers.ModelSerializer):

    class Meta:
        model = Triple
        fields = ['subject', 'predicate', 'object']



class MetaDataSerializer(serializers.HyperlinkedModelSerializer):
    creators = CreatorSerializer(many=True, )
    modified = DateSerializer(many=True)


    class Meta:
        model = MetaData
        fields = ['description', 'creators', 'created', 'modified']

    def get(self,validated_data):
        return MetaData.objects.get(**validated_data)

    def update(self, instance, validated_data):
        instance.description = validated_data.get("description", instance.description)
        instance.creators = validated_data.get("creators", instance.creators)
        instance.created = validated_data.get("created", instance.created)
        instance.modified = validated_data.get("modified", instance.modified)







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


    def get(self,validated_data):
        return ArchiveEntry.objects.get(**validated_data)



    def update(self,instance,validated_data):
        """

        :param validated_data:
        :return:
        """

        instance.archive = validated_data.get('archive', instance.archive)
        instance.location = validated_data.get('location', instance.location)
        instance.format = validated_data.get('format', instance.format)
        instance.master = validated_data.get('master', instance.master)
        instance.metadata = validated_data.get('metadata', instance.metadata)
        return instance

    class Meta:
        model = ArchiveEntry
        fields = ['archive', 'location', 'format', 'master', 'metadata']






class UserSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializing all Users. """
    url = serializers.HyperlinkedIdentityField(view_name='api:user-detail')

    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']


