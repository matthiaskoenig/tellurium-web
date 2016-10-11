from django import forms


class UploadArchiveForm(forms.Form):
    # name = forms.CharField(max_length=50)
    file = forms.FileField(
        label='Select a CombineArchive file',
        help_text='max. 42 megabytes'
    )
