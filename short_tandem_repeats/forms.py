from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from short_tandem_repeats.models import STRFile


class STRFileForm(ModelForm):
    class Meta:
        model = STRFile
        fields = ["file"]
        labels = {"file": _("Excel file with short tandem repeats")}
