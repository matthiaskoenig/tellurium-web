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
