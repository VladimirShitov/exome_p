from pathlib import Path

from django.core.validators import FileExtensionValidator
from django.db import models

from .validators import check_vcf_format


class VCFFile(models.Model):
    file = models.FileField(
        upload_to=Path('raw_data/vcf/'),
        validators=[
            check_vcf_format,
            FileExtensionValidator(allowed_extensions=['vcf', 'vcf.gz', 'bcf']),
        ]
    )
