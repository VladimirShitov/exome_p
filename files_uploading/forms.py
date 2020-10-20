from django.db import transaction
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from loguru import logger
from pysam import VariantFile
from typing import Optional

from .models import VCFFile
from .utils import are_samples_empty, parse_samples, save_record_to_db
from .types import SamplesDict


class VCFFileForm(ModelForm):
    class Meta:
        model = VCFFile
        fields = ['file']
        labels = {'file': _('File with genetic variants (e.g. VCF file)')}

    def save(self, commit=True):
        with transaction.atomic():
            vcf_file: VCFFile = super().save(commit=commit)
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