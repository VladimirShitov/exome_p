from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import check_vcf_format


def get_deleted_sample():
    return Sample.objects.get_or_create(cypher='deleted')


class VCFFile(models.Model):
    file = models.FileField(
        upload_to='raw_data/vcf/',
        validators=[
            check_vcf_format,
            FileExtensionValidator(allowed_extensions=['vcf', 'vcf.gz', 'bcf']),
        ]
    )


class Allele(models.Model):
    variant = models.CharField(max_length=15, blank=False, primary_key=True)


class SNP(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    reference_allele = models.ForeignKey(to=Allele, on_delete=models.CASCADE, related_name='REF')
    alternative_allele = models.ForeignKey(to=Allele, on_delete=models.CASCADE, related_name='ALT')


class Chromosome(models.Model):
    number = models.SmallIntegerField(primary_key=True)


class AllelesRecord(models.Model):
    record = models.CharField(max_length=15, blank=False, primary_key=True)


class Variant(models.Model):
    chromosome_number = models.ForeignKey(to=Chromosome, on_delete=models.CASCADE)
    position = models.IntegerField(blank=False)
    alleles_record = models.ForeignKey(
        to=AllelesRecord, on_delete=models.SET_NULL, null=True, blank=True
    )
    snp = models.ForeignKey(to=SNP, on_delete=models.SET_NULL, null=True, blank=True)


class Nationality(models.Model):
    nationality = models.CharField(max_length=255, blank=True, null=True)


class MitochondriaHaplogroup(models.Model):
    haplogroup = models.CharField(max_length=255)


class YHaplogroup(models.Model):
    haplogroup = models.CharField(max_length=255)


class Sample(models.Model):

    class Gender(models.TextChoices):
        FEMALE = 'F', _('Female')
        MALE = 'M', _('Male')
        OTHER = 'O', _('Other')
        UNDEFINED = 'U', _('Undefined')

    cypher = models.CharField(max_length=255)
    gender = models.CharField(max_length=15, choices=Gender.choices, default=Gender.UNDEFINED)
    nationality = models.ForeignKey(
        to=Nationality, on_delete=models.SET_NULL, null=True, blank=True
    )
    mitochondrial_haplogroup = models.ForeignKey(
        to=MitochondriaHaplogroup, on_delete=models.SET_NULL, null=True
    )
    Y_haplogroup = models.ForeignKey(
        to=YHaplogroup, on_delete=models.SET_NULL, null=True, blank=True
    )
    vcf_file = models.ForeignKey(to=VCFFile, on_delete=models.SET_NULL, null=True, blank=True)
