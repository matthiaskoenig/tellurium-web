"""
Forms.
"""
from django import forms
from . import validators
import requests
from django.core.files import File
import io

class UploadArchiveForm(forms.Form):
    # name = forms.CharField(max_length=50)
    url = forms.URLField(
        validators=[validators.validate_url_omex,],
        required=False
    )

    file = forms.FileField(
        #widget=forms.ClearableFileInput(attrs={'multiple': True}),
        #widget=forms.FileInput(attrs={'class': "btn btn-primary"}),

        label='Drag & Drop or select archive',
        help_text="max. 100 MB, content type: application/zip",
        validators=[validators.validate_omex,],
        required=False)

    def clean_url(self):
        url = self.data.get("url")
        if  bool(url):
            validators.validate_url_omex(url)
        return url

    def clean(self):
        cleaned_data = super().clean()
        file = self.files.get("file")
        url = self.data.get("url")
        if not (bool(file) or  bool(url)):
            msg = "One of these two fields needs an input!"
            self.add_error('file', msg)
            self.add_error('url', msg)

        elif (bool(file) and  bool(url)):
             msg = "Select only one Field."
             self.add_error('file', msg)
             self.add_error('url', msg)

        elif not bool(file):
                import re
                def get_filename_from_cd(cd):
                    """
                    Get filename from content-disposition
                    """
                    if not cd:
                        return None
                    fname = re.findall('filename=(.+)', cd)
                    if len(fname) == 0:
                        return None
                    return fname[0]

                r = requests.get(url, allow_redirects=True)
                filename = get_filename_from_cd(r.headers.get('content-disposition'))
                f = io.BytesIO()
                f.name = filename
                f.write(r.content)
                validators.validate_omex(File(f))

                self.cleaned_data["file"] = f


        return super().clean()














