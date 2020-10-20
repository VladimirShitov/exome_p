from loguru import logger
from pysam import VariantRecord
from typing import Optional

from .models import Allele, Chromosome, Sample, SNP, VCFFile
from .types import SamplesDict


def are_samples_empty(record: VariantRecord):
    if not record.samples.items():
        logger.warning('No samples detected')
        logger.info('Finishing reading the file')


def parse_samples(record: VariantRecord, vcf_file: VCFFile) -> Optional[SamplesDict]:
    samples: Optional[SamplesDict] = {}

    for sample_name, sample in record.samples.items():
        # Put samples in a dict so that we don't go to db each time
        sample_db_record, is_sample_created = Sample.objects.get_or_create(
            cypher=sample_name
        )
        if is_sample_created:
            sample_db_record.vcf_file = vcf_file
            sample_db_record.save()
            samples[sample_name] = sample_db_record
        else:
            logger.warning(  # TODO: handle it smarter
                'Sample {} already exists in the database. Ignoring', sample_name
            )

    return samples


def create_snp(chromosome: Chromosome, record: VariantRecord, ref: Allele, alt: Allele) -> SNP:
    snp, created = SNP.objects.get_or_create(
        chromosome=chromosome,
        position=record.pos,
        reference_allele=ref,
        alternative_allele=alt,
    )

    if not snp.name and record.id:
        snp.name = record.id
        snp.save()

    if record.id is not None and snp.name != record.id:
        logger.warning(
            "SNP names' conflict. Old name: {}, new name: {}", snp.name, record.id
        )

    return snp
