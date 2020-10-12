from django.core.validators import FileExtensionValidator
from django.db import models

from .validators import check_vcf_format


class VCFFile(models.Model):
    file = models.FileField(
        validators=[
            check_vcf_format,
            FileExtensionValidator(allowed_extensions=['vcf', 'vcf.gz', 'bcf']),
        ]
    )
