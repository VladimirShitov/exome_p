from loguru import logger
from pysam import VariantRecord


def are_samples_empty(record: VariantRecord):
    if not record.samples.items():
        logger.warning('No samples detected')
        logger.info('Finishing reading the file')
