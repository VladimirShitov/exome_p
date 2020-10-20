from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from pysam import VariantRecord

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
    genotype = models.CharField(max_length=15, blank=False, primary_key=True)


class Chromosome(models.Model):

    number = models.SmallIntegerField(primary_key=True)

    @classmethod
    def from_record(cls, record: VariantRecord):
        chromosome, created = cls.objects.get_or_create(
            number=cls.NamesMapper.name_to_number(name=record.chrom)
        )
        return chromosome

    class NamesMapper:
        names_to_number_map = {f'chr{i}': i for i in range(1, 23)}
        names_to_number_map.update(
            {'X': 23, 'chrX': 23, 'Y': 24, 'chrY': 24, 'XY': 25, 'chrXY': 25, 'chrM': 26, 'MT': 26}
        )

        @classmethod
        def name_to_number(cls, name):
            return cls.names_to_number_map[name]


class SNP(models.Model):
    class Meta:
        unique_together = (
            ('chromosome', 'position', 'reference_allele', 'alternative_allele'),
        )
    name = models.CharField(max_length=255, blank=True)
    chromosome = models.ForeignKey(to=Chromosome, on_delete=models.CASCADE)
    position = models.IntegerField(blank=False)
    reference_allele = models.ForeignKey(
        to=Allele, on_delete=models.CASCADE, related_name='ref_to_snp'
    )
    alternative_allele = models.ForeignKey(
        to=Allele, on_delete=models.CASCADE, related_name='alt_to_snp'
    )


class AllelesRecord(models.Model):

    @staticmethod
    def from_tuple(alleles):
        if alleles == (None, None):
            return 'Undefined'

        if alleles == (1, 0):
            return '0/1'
        return '/'.join(map(str, alleles))

    record = models.CharField(max_length=15, blank=False, primary_key=True)


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

    cypher = models.CharField(max_length=255, primary_key=True)
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


class Variant(models.Model):
    alleles_record = models.ForeignKey(
        to=AllelesRecord, on_delete=models.SET_NULL, null=True, blank=True
    )
    sample = models.ForeignKey(to=Sample, on_delete=models.CASCADE)
    snp = models.ForeignKey(to=SNP, on_delete=models.SET_NULL, null=True, blank=True)
