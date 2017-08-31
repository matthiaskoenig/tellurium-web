
from __future__ import print_function, absolute_import
from django import forms
# import libcombine
from django.core.validators import ValidationError


class UploadArchiveForm(forms.Form):
    # name = forms.CharField(max_length=50)
    file = forms.FileField(
        label='Drag & Drop or select file (*.omex)',
        help_text='max. 42 Mb'
    )

    # def clean_file(self):
    #     """ Validates the archive using libcombine.
    #
    #     :return:
    #     """
    #     file = self.cleaned_data['file']
    #     print(file.path)
    #
    #     # Try to read the archive
    #     omex = libcombine.CombineArchive()
    #     if not omex.initializeFromArchive(str(file.path)):
    #         print("Invalid Combine Archive")
    #         raise ValidationError(
    #             _('Invalid archive: %(file)s'),
    #             code='invalid',
    #             params={'file': 'file'},
    #         )
    #
    #     return file
