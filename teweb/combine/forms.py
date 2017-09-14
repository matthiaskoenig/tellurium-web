"""
Forms.
"""
from django import forms
from . import validators


class UploadArchiveForm(forms.Form):
    # name = forms.CharField(max_length=50)
    file = forms.FileField(
        label='Drag & Drop or select archive',
        help_text="max. 100 MB, content type: application/zip",
        validators=[validators.validate_omex]
    )



