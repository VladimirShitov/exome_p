from loguru import logger
from pysam import VariantRecord
from typing import Optional

from .models import Sample, VCFFile
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
