from django.forms import ModelForm

from .models import VCFFile


class VCFFileForm(ModelForm):
    class Meta:
        model = VCFFile
        fields = ['file']
