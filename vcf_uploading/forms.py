from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Allele, Chromosome, RawVCF


class VCFFileForm(ModelForm):
    class Meta:
        model = RawVCF
        fields = ["file"]
        labels = {"file": _("File with genetic variants (e.g. VCF file)")}


class SNPSearchForm(forms.Form):
    chromosome = forms.ModelChoiceField(
        queryset=Chromosome.objects.all(),
        empty_label=None,
        required=True,
        label=_("Chromosome"),
    )
    position = forms.IntegerField(
        min_value=0, max_value=3.5 * 10 ** 9, required=True, label=_("Position")
    )
    allele_1 = forms.ModelChoiceField(
        queryset=Allele.objects.all(),
        empty_label=None,
        required=True,
        label=_("The first allele"),
    )
    allele_2 = forms.ModelChoiceField(
        queryset=Allele.objects.all(),
        empty_label=None,
        required=True,
        label=_("The second allele"),
    )
