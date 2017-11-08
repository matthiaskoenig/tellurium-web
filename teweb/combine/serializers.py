from rest_framework import serializers
from .models import Tag,Archive
from django.contrib.auth.models import User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name', 'type','uuid']

class ArchiveSerializer(serializers.HyperlinkedModelSerializer):
    tags = serializers.HyperlinkedRelatedField(many=True, view_name='api:tag-detail', queryset=Tag.objects.all(),  lookup_field='uuid')
    user = serializers.HyperlinkedRelatedField(view_name='api:user-detail',read_only=True)


    #tags = serializers.StringRelatedField(many=True)
    class Meta:
        model = Archive
        fields = ['name','file','created','md5','task_id','tags','uuid','user']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:user-detail')

    class Meta:
        model = User
        fields = ['url','username', 'email', 'is_staff']
