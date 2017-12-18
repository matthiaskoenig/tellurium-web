"""
Admin pages.
"""
from django.contrib import admin

from .models import Archive, Tag, Creator, Triple, ArchiveEntry, MetaData, Date


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'file', 'created', 'md5_short', 'task_id', 'user', 'uuid')
    list_filter = ('user',)
    fields = ('name', 'file', 'user', 'tags')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'uuid')
    list_filter = ('category',)
    fields = ('name', 'category')


@admin.register(ArchiveEntry)
class ArchiveEntryAdmin(admin.ModelAdmin):
    list_display = ('archive', 'location', 'file', 'base_format', 'short_format', 'format', 'master', 'metadata')
    list_filter = ('master',)
    fields = ('archive', 'location', 'format', 'master')


@admin.register(Date)
class DateAdmin(admin.ModelAdmin):
    list_display = ('date',)
    fields = ('date',)


@admin.register(Triple)
class TripleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'predicate', 'object')
    list_filter = ('predicate',)
    fields = ('subject', 'predicate', 'object')


@admin.register(Creator)
class CreatorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'organisation', 'email')
    list_filter = ('organisation',)
    fields = ('first_name', 'last_name', 'organisation', 'email')


@admin.register(MetaData)
class MetaDataAdmin(admin.ModelAdmin):
    list_display = ('description', 'created')
    fields = ('description', 'creators')
