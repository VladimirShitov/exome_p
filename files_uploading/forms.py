from django import forms
from django.db import transaction
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from loguru import logger
from pysam import VariantFile
from typing import Optional

from .models import Allele, Chromosome, RawVCF
from .utils import are_samples_empty, parse_samples, save_record_to_db
from .types import SamplesDict


class VCFFileForm(ModelForm):
    class Meta:
        model = RawVCF
        fields = ['file']
        labels = {'file': _('File with genetic variants (e.g. VCF file)')}

    def save(self, commit=True):
        with transaction.atomic():
            vcf_file: RawVCF = super().save(commit=commit)
            logger.info('Trying to read VCF file with pysam')
            vcf: VariantFile = VariantFile(vcf_file.file.path)

            with transaction.atomic():
                first_iteration = True

                for i, record in enumerate(vcf.fetch()):
                    if i % 100 == 1:
                        logger.debug("{} records processed", i)

                    if first_iteration:
                        if are_samples_empty(record):
                            break
                        samples: Optional[SamplesDict] = parse_samples(record, vcf_file)
                        if not samples:
                            logger.info('No new samples detected. Breaking')
                            break
                        first_iteration = False

                    save_record_to_db(record=record, samples=samples)


class SNPSearchForm(forms.Form):
    chromosome = forms.ModelChoiceField(
        queryset=Chromosome.objects.all(), empty_label=None, required=True, label=_('Chromosome')
    )
    position = forms.IntegerField(
        min_value=0, max_value=3.5*10**9, required=True, label=_('Position')
    )
    allele_1 = forms.ModelChoiceField(
        queryset=Allele.objects.all(), empty_label=None, required=True, label=_('The first allele')
    )
    allele_2 = forms.ModelChoiceField(
        queryset=Allele.objects.all(),
        empty_label=None,
        required=True,
        label=_("The second allele"),
    )
