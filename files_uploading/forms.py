from django.db import transaction
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from loguru import logger
from pysam import VariantFile
from typing import Optional

from .models import (
    VCFFile,
    Allele,
    Chromosome,
    AllelesRecord,
    Variant,
    SNP,
)
from .utils import are_samples_empty, parse_samples
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
                samples = {}

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

                    chromosome: Chromosome = Chromosome.from_record(record)

                    reference_allele = Allele.objects.get_or_create(genotype=record.ref)

                    for sample_name, sample in record.samples.items():
                        alleles_record, created = AllelesRecord.objects.get_or_create(
                            record=AllelesRecord.from_tuple(sample.allele_indices)
                        )

                    if len(record.alts) > 1:
                        logger.warning("Multiple alternative alleles!")

                    alt = record.alts[0]

                    alternative_allele, created = Allele.objects.get_or_create(genotype=alt)

                    snp, created = SNP.objects.get_or_create(
                        chromosome=chromosome,
                        position=record.pos,
                        reference_allele=reference_allele,
                        alternative_allele=alternative_allele,
                    )
                    if not snp.name and record.id:
                        snp.name = record.id
                        record.save()
                    if record.id is not None and snp.name != record.id:
                        logger.warning(
                            "SNP names' conflict. Old name: {}, new name: {}", snp.name, record.id
                        )

                    for sample_name, sample_db_record in samples.items():
                        variant, created = Variant.objects.get_or_create(
                            alleles_record=alleles_record,
                            snp=snp,
                            sample=sample_db_record,
                        )
