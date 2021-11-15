from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from short_tandem_repeats.models import STRFile, ShortTandemRepeat, STRRegion


class STRFileForm(ModelForm):
    class Meta:
        model = STRFile
        fields = ["file"]
        labels = {"file": _("Excel file with short tandem repeats")}


class STRSearchForm(forms.Form):
    region = forms.ModelChoiceField(
        queryset=STRRegion.objects.all(),
        empty_label=None,
        required=True,
        label=_("Region"),
    )
    n_repeats = forms.IntegerField(
        min_value=0, max_value=3.5 * 10 ** 5, required=True, label=_("Number of repeats")
    )
