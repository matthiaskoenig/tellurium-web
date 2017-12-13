"""
Admin pages.
"""
from django.contrib import admin

from .models import Archive, Tag, Creator, Triple, ArchiveEntry, ArchiveEntryMeta


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = ('name', 'file', 'created', 'md5_short', 'task_id', 'user', 'uuid')
    list_filter = ('user',)
    fields = ('name', 'file', 'user', 'tags')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'uuid')
    list_filter = ('category',)
    fields = ('name', 'category')


@admin.register(Creator)
class CreatorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'organisation', 'email')
    list_filter = ('organisation',)
    fields = ('first_name', 'last_name', 'organisation', 'email')


@admin.register(Triple)
class TripleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'predicate', 'object')
    list_filter = ('predicate',)
    fields = ('subject', 'predicate', 'object')


@admin.register(ArchiveEntry)
class ArchiveEntryAdmin(admin.ModelAdmin):
    list_display = ('archive', 'location', 'format', 'master')
    list_filter = ('format', 'master')
    fields = ('archive', 'location', 'format', 'master')


@admin.register(ArchiveEntryMeta)
class ArchiveEntryMetaAdmin(admin.ModelAdmin):
    list_display = ('entry', 'description', 'created')
    fields = ('entry', 'description', 'creators')
