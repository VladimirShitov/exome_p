from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import VCFFile


class VCFFileForm(ModelForm):
    class Meta:
        model = VCFFile
        fields = ['file']
        labels = {'file': _('File with genetic variants (e.g. VCF file)')}
