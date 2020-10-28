from typing import Dict, List, Tuple

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from loguru import logger
from pysam.libcbcf import VariantRecord, VariantRecordSample


def get_deleted_sample():
    return Sample.objects.get_or_create(cypher='deleted')


class VCFFile(models.Model):
    from .validators import check_vcf_format

    file = models.FileField(
        upload_to='raw_data/vcf/',
        validators=[
            check_vcf_format,
            FileExtensionValidator(allowed_extensions=['vcf', 'vcf.gz', 'bcf', 'gz']),
        ]
    )


class Allele(models.Model):
    genotype = models.CharField(max_length=15, blank=False, primary_key=True)

    @classmethod
    def from_str(cls, genotype: str):
        allele, created = cls.objects.get_or_create(genotype=genotype)
        return allele

    @classmethod
    def ref_from_record(cls, record: VariantRecord):
        allele, created = cls.objects.get_or_create(genotype=record.ref)
        return allele

    @classmethod
    def alt_from_record(cls, record: VariantRecord):
        if len(record.alts) > 1:
            logger.warning("Multiple alternative alleles!")
        alt = record.alts[0]
        allele, created = cls.objects.get_or_create(genotype=alt)

        return allele

    def __str__(self):
        return str(self.genotype)


class Chromosome(models.Model):

    number = models.SmallIntegerField(primary_key=True)

    @classmethod
    def from_record(cls, record: VariantRecord):
        chromosome, created = cls.objects.get_or_create(
            number=cls.NamesMapper.name_to_number(name=record.chrom)
        )
        return chromosome

    class NamesMapper:
        names_to_number_map: Dict[str, int] = {}
        numbers_to_name_map: Dict[int, str] = {}

        for i in range(1, 23):
            names_to_number_map[f'chr{i}'] = i
            numbers_to_name_map[i] = str(i)

        names_to_number_map.update(
            {'X': 23, 'chrX': 23, 'Y': 24, 'chrY': 24, 'XY': 25, 'chrXY': 25, 'chrM': 26, 'MT': 26}
        )
        numbers_to_name_map.update(
            {23: 'X', 24: 'Y', 25: 'XY', 26: 'M'}
        )

        @classmethod
        def name_to_number(cls, name):
            return cls.names_to_number_map[name]

        @classmethod
        def number_to_name(cls, number):
            return cls.numbers_to_name_map[number]

    def __str__(self):
        return self.NamesMapper.number_to_name(self.number)


class AllelesRecord(models.Model):
    record = models.CharField(max_length=15, blank=False, primary_key=True)

    @staticmethod
    def from_tuple(alleles):
        if alleles == (None, None):
            return 'Undefined'

        if alleles == (1, 0):
            return '0/1'
        return '/'.join(map(str, alleles))

    @classmethod
    def from_sample(cls, sample: VariantRecordSample):
        alleles_record, created = cls.objects.get_or_create(
            record=cls.from_tuple(sample.allele_indices)
        )
        return alleles_record

    def __str__(self):
        return self.record


class Nationality(models.Model):
    nationality = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nationality


class MitochondriaHaplogroup(models.Model):
    haplogroup = models.CharField(max_length=255)

    def __str__(self):
        return self.haplogroup


class YHaplogroup(models.Model):
    haplogroup = models.CharField(max_length=255)

    def __str__(self):
        return self.haplogroup


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

    def __str__(self):
        return self.cypher


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

    def __str__(self):
        return f'{self.name} chr{self.chromosome} {self.position} ' \
               f'REF: {self.reference_allele} ALT: {self.alternative_allele}'

    def get_samples(self) -> List[Sample]:
        variants_with_snp = Variant.objects.filter(snp=self).select_related('sample')
        samples = [v.sample for v in variants_with_snp]
        return samples


class Variant(models.Model):
    from .metrics import identity_percentage

    alleles_record = models.ForeignKey(
        to=AllelesRecord, on_delete=models.SET_NULL, null=True, blank=True
    )
    sample = models.ForeignKey(to=Sample, on_delete=models.CASCADE)
    snp = models.ForeignKey(to=SNP, on_delete=models.SET_NULL, null=True, blank=True)
    alleles = models.ManyToManyField(to=Allele)

    def get_genotype_string(self):
        alleles = self.alleles.all()

        if len(alleles) == 1:
            genotype = f'{alleles[0]}, {alleles[0]}'
        else:
            genotype = ', '.join(str(allele) for allele in alleles) or 'unknown'
        return genotype

    def __str__(self):
        return f'Sample: {self.sample}, SNP: {self.snp}, genotype: {self.alleles_record} (' \
               f'{self.get_genotype_string()})'

    def calculate_similarity(
            self, alleles: Tuple[Allele], metric=identity_percentage
    ) -> float:
        variant_alleles = tuple(self.alleles.all())

        if all(allele is None for allele in variant_alleles):
            return 0

        return metric(variant_alleles, alleles)



