from typing import List

from django.db import transaction
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from loguru import logger
from pysam import VariantFile

from .models import (
    VCFFile,
    Allele,
    Chromosome,
    AllelesRecord,
    Variant,
    Sample,
    SNP,
)


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
                samples = {}

                for i, record in enumerate(vcf.fetch()):
                    if i % 50 == 1:
                        logger.debug("{} records processed", i)

                    if first_iteration:
                        if not record.samples.items():
                            logger.warning('No samples detected')
                            logger.info('Finishing reading the file')
                            break

                        for sample_name, sample in record.samples.items():
                            # We can put samples in a dict so that we don't go to db each time
                            sample_db_record, is_sample_created = Sample.objects.get_or_create(
                                cypher=sample_name
                            )
                            if is_sample_created:
                                sample_db_record.vcf_file = vcf_file
                                sample_db_record.save()
                                samples[sample_name] = sample_db_record
                            else:
                                logger.warning(  # TODO: handle it smarter
                                    'Sample {} already exists in the database. Ignoring',
                                    sample_name
                                )

                        first_iteration = False
                        logger.debug(samples)

                        if not samples:
                            logger.info('No new samples detected. Breaking')
                            break
