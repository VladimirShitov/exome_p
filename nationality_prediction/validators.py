import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _
from loguru import logger
from pysam import VariantFile


def check_number_of_samples(file: InMemoryUploadedFile):
    with tempfile.NamedTemporaryFile(suffix=".vcf") as f:
        f.write(file.read())
        file.seek(0)

        logger.info("Saved VCF to the temporary file {}", f.name)
        logger.debug("Is file readable: {}", f.readable())

        try:
            vcf = VariantFile(f.name)
        except (ValueError, OSError) as e:
            raise ValidationError(
                _(
                    "Reading of the file has failed. Probably, the file has a wrong format"
                ),
                code="format.invalid",
            ) from e

        record = next(vcf.fetch())
        samples = record.samples

        if len(samples) > 1:
            raise ValidationError(
                _(
                    "Uploaded file has more than 1 sample. Number of samples: %(n_samples)s"
                ),
                params={"n_samples": len(samples)},
                code="samples.number.invalid",
            )
