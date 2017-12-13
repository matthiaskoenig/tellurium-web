"""
Admin pages.
"""
from django.contrib import admin

from .models import Archive, Tag, Creator, Triple, ArchiveEntry, ArchiveEntryMeta

@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = ('name', 'file', 'created', 'md5_short', 'task_id', 'user', 'uuid')
    list_filter = ('user',)
    fields = ('name', 'file', 'user')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'uuid')
    list_filter = ('category',)
    fields = ('name', 'category')
