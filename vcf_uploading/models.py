from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from loguru import logger
from pysam.libcbcf import VariantFile, VariantRecord, VariantRecordSample

from nationality_prediction.predictors import FastNGSAdmixPredictor
from vcf_uploading.vcf_processing import VCFFile, VCFRecord


def get_deleted_sample():
    return Sample.objects.get_or_create(cypher="deleted")


class RawVCF(models.Model):
    class VCFTimeCheckingManager(models.Manager):
        _TIME_THRESHOLD = timedelta(minutes=45)

        def get_queryset(self):
            """Return only files that were uploaded recently or are already saved

            Files that were uploaded earlier that current time - `self._TIME_THRESHOLD`
            are deleted in this query
            """
            keep_files_after = timezone.now() - self._TIME_THRESHOLD

            not_saved_vcfs = (
                super()
                .get_queryset()
                .filter(date_created__lt=keep_files_after, saved=False)
            )
            deletion_log = not_saved_vcfs.delete()
            logger.info("Deleted not saved VCF: {}", deletion_log)

            return (
                super()
                .get_queryset()
                .filter(Q(saved=True) | Q(date_created__gte=keep_files_after))
            )

    from .validators import check_vcf_format

    file = models.FileField(
        upload_to="raw_data/vcf/",
        validators=[
            check_vcf_format,
            FileExtensionValidator(allowed_extensions=["vcf", "vcf.gz", "bcf", "gz"]),
        ],
    )
    date_created = models.DateTimeField(auto_now_add=True)
    saved = models.BooleanField(default=False)
    n_samples = models.IntegerField(blank=True, null=True)
    n_refs = models.IntegerField(blank=True, null=True)
    n_alts = models.IntegerField(blank=True, null=True)
    n_missing_genotypes = models.IntegerField(blank=True, null=True)
    objects = VCFTimeCheckingManager()

    def calculate_statistics(self):
        """Calculate statistics of VCF file

        The following statistics are calculated
        1. Number of samples in file
        2. Number of REF matches
        3. Number of ALTs
        4. Number of missing genotypes

        :return samples_statistics: Dict[str, SampleStatistics]. Keys of the dictionary
          are samples' names. Values are dictionaries with keys:
          * n_refs: int — number of alleles that are identical to a reference
          * n_alts: int — number of alleles that are not identical to a reference
          * n_missing: int — number of alleles with unknown genotype
        """
        from vcf_uploading.types import SampleStatistics

        logger.info("Trying to read VCF file with pysam")
        vcf: VariantFile = VariantFile(self.file.path)

        self.n_refs = 0
        self.n_missing_genotypes = 0
        self.n_alts = 0
        self.n_samples = 0
        self.n_records = 0

        samples_statistics: Dict[str, SampleStatistics] = {}

        for i, record in enumerate(vcf.fetch()):
            for sample in record.samples:
                indices: Tuple[int] = record.samples[
                    sample
                ].allele_indices  # e.g. (0, 1)

                n_refs = indices.count(0)
                n_missing = indices.count(None)
                n_alts = 2 - n_refs - n_missing

                self.n_refs += n_refs
                self.n_missing_genotypes += n_missing
                self.n_alts += n_alts

                if sample in samples_statistics:  # TODO: can we make it a defaultdict?
                    samples_statistics[sample]["n_refs"] += n_refs
                    samples_statistics[sample]["n_alts"] += n_alts
                    samples_statistics[sample]["n_missing"] += n_missing
                else:
                    samples_statistics[sample] = {}
                    samples_statistics[sample]["n_refs"] = 0
                    samples_statistics[sample]["n_alts"] = 0
                    samples_statistics[sample]["n_missing"] = 0

        if "record" in locals():  # Cycle executed at least once
            self.n_samples = len(record.samples)
            self.n_records = i + 1

        self.save()

        return samples_statistics

    def save_samples_to_db(self):
        from vcf_uploading.types import SamplesDict
        from vcf_uploading.utils import are_samples_empty, parse_samples, save_record_to_db

        with transaction.atomic():
            self.saved = True
            self.save()

            logger.info("Trying to read VCF file with pysam")
            vcf: VariantFile = VariantFile(self.file.path)

            with transaction.atomic():
                first_iteration = True

                for i, record in enumerate(vcf.fetch()):
                    if i % 100 == 1:
                        logger.debug("{} records processed", i)

                    if first_iteration:
                        if are_samples_empty(record):
                            break
                        samples: Optional[SamplesDict] = parse_samples(record, self)
                        if not samples:
                            logger.info("No new samples detected. Breaking")
                            break
                        first_iteration = False

                    save_record_to_db(record=record, samples=samples)

                logger.info("File is saved to the database")
                logger.debug("File.saved: {}", self.saved)

    def get_samples(self) -> List[str]:
        vcf_file_path = Path(self.file.path)

        pysam_vcf: VariantFile = VariantFile(vcf_file_path)
        record = next(pysam_vcf.fetch())
        samples: List[str] = list(record.samples.keys())

        pysam_vcf.close()

        return samples

    def predict_nationality(self) -> Dict[str, Dict[str, float]]:
        """Predict nationalities for each sample in `self.file`

        :return samples_nationalities: Dict[str, Dict[str, float]] - a dictionary,
            where the keys are the samples, and the values are the prediction of
            nationalities. In the predictions, keys are nationalities, and values
            are their probabilities
        """
        logger.info("Predicting nationality for RawVCF")

        predictions = {}

        for sample in self.get_samples():
            logger.info("Predicting nationality for sample {}", sample)
            sample_vcf: VariantFile = VariantFile(self.file.path)
            sample_vcf.subset_samples([sample])

            predictor = FastNGSAdmixPredictor(sample_vcf)
            predictions[sample] = predictor.predict()

            sample_vcf.close()

        logger.info("Returning nationality predictions")
        logger.debug("Predictions: {}", predictions)
        return predictions

    def find_similar_samples_in_db(self):
        from .utils import get_average_similarities
        logger.info("Trying to find similar samples in the DB for file {}", self.file.name)
        similar_samples: Dict[str, Dict[str, List[float]]] = {}

        samples = self.get_samples()

        for sample in samples:
            similar_samples[sample] = defaultdict(list)

        vcf: VariantFile = VariantFile(self.file.path)
        # TODO: this can be done MUCH faster
        # We can check for a few tens of SNPs from file. If a database
        # sample has different genotypes in most of them, we can exclude it
        # from the further checks
        for i, record in enumerate(vcf):
            if i % 100 == 1:
                logger.info("{} records processed", i)
            snp = SNP.from_record(record)

            for sample_name, sample in record.samples.items():
                if snp is None:
                    for db_sample in Sample.objects.all():
                        similar_samples[sample_name][db_sample.cypher].append(0)
                else:
                    if all(allele is None for allele in sample.alleles):
                        continue
                    db_samples_similarity = SNP.calculate_similarity_to_each_sample(
                        snp, sample.alleles
                    )
                    for db_sample, similarity in db_samples_similarity.items():
                        similar_samples[sample_name][db_sample].append(similarity)

        similarities: Dict[str, Dict[str, float]] = get_average_similarities(similar_samples)
        return similarities


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
        try:
            chromosome, created = cls.objects.get_or_create(
                number=cls.NamesMapper.name_to_number(name=record.chrom)
            )

        except KeyError as e:  # Maybe chromosome is written as a number
            try:
                chromosome_number = int(record.chrom)
            except ValueError as value_error:
                raise ValueError(
                    _(f"{record.chrom} is not a valid chromosome name")
                ) from value_error

            if chromosome_number in cls.NamesMapper.numbers_to_name_map.keys():
                chromosome, created = cls.objects.get_or_create(
                    number=chromosome_number
                )
            else:
                raise ValueError(
                    _(f"{record.chrom} is not a valid chromosome name")
                ) from e

        return chromosome

    class NamesMapper:
        names_to_number_map: Dict[str, int] = {}
        numbers_to_name_map: Dict[int, str] = {}

        for i in range(1, 23):
            names_to_number_map[f"chr{i}"] = i
            numbers_to_name_map[i] = str(i)

        names_to_number_map.update(
            {
                "X": 23,
                "chrX": 23,
                "Y": 24,
                "chrY": 24,
                "XY": 25,
                "chrXY": 25,
                "chrM": 26,
                "MT": 26,
            }
        )
        numbers_to_name_map.update({23: "X", 24: "Y", 25: "XY", 26: "M"})

        @classmethod
        def name_to_number(cls, name):
            return cls.names_to_number_map[name]

        @classmethod
        def number_to_name(cls, number: int):
            return cls.numbers_to_name_map[number]

    def __str__(self):
        return self.NamesMapper.number_to_name(self.number)


class AllelesRecord(models.Model):
    record = models.CharField(max_length=15, blank=False, primary_key=True)

    @staticmethod
    def from_tuple(alleles):
        if alleles == (None, None):
            return "./."

        if alleles == (1, 0):
            return "0/1"
        return "/".join(map(str, alleles))

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
        FEMALE = "F", _("Female")
        MALE = "M", _("Male")
        OTHER = "O", _("Other")
        UNDEFINED = "U", _("Undefined")

    cypher = models.CharField(max_length=255, primary_key=True)
    gender = models.CharField(
        max_length=15, choices=Gender.choices, default=Gender.UNDEFINED
    )
    nationality = models.ForeignKey(
        to=Nationality,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sample",
    )
    predicted_nationality = models.ForeignKey(
        to=Nationality,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="predicted_nationality_sample",
    )
    mitochondrial_haplogroup = models.ForeignKey(
        to=MitochondriaHaplogroup, on_delete=models.SET_NULL, null=True
    )
    Y_haplogroup = models.ForeignKey(
        to=YHaplogroup, on_delete=models.SET_NULL, null=True, blank=True
    )
    vcf_file = models.ForeignKey(
        to=RawVCF, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.cypher

    def to_vcf(self) -> VCFFile:
        vcf_file = VCFFile(sample=str(self))

        variants = Variant.objects.filter(sample=self).select_related("snp")

        for variant in variants:
            vcf_record = VCFRecord(
                chromosome=str(variant.snp.chromosome),
                position=variant.snp.position,
                sample=str(self),
                sample_indexes=variant.alleles_record,
                ref=str(variant.snp.reference_allele),
                alts=[str(variant.snp.alternative_allele)],
                id_=variant.snp.name,
            )
            vcf_file.add_record(vcf_record)

        return vcf_file

    def predict_nationality(self):
        predictor = FastNGSAdmixPredictor(self.to_vcf())
        return predictor.predict()


class SNP(models.Model):
    class Meta:
        unique_together = (
            ("chromosome", "position", "reference_allele", "alternative_allele"),
        )

    name = models.CharField(max_length=255, blank=True)
    chromosome = models.ForeignKey(to=Chromosome, on_delete=models.CASCADE)
    position = models.IntegerField(blank=False)
    reference_allele = models.ForeignKey(
        to=Allele, on_delete=models.CASCADE, related_name="ref_to_snp"
    )
    alternative_allele = models.ForeignKey(
        to=Allele, on_delete=models.CASCADE, related_name="alt_to_snp"
    )

    def __str__(self):
        return (
            f"{self.name} chr{self.chromosome} {self.position} "
            f"REF: {self.reference_allele} ALT: {self.alternative_allele}"
        )

    def get_samples(self) -> List[Sample]:
        variants_with_snp = Variant.objects.filter(snp=self).select_related("sample")
        samples = [v.sample for v in variants_with_snp]
        return samples

    @classmethod
    def from_record(cls, record: VariantRecord) -> Optional["SNP"]:
        position = record.pos
        chromosome = Chromosome.from_record(record)
        ref_allele = Allele.ref_from_record(record)
        alt_allele = Allele.alt_from_record(record)
        try:
            return SNP.objects.get(
                position=position,
                chromosome=chromosome,
                reference_allele=ref_allele,
                alternative_allele=alt_allele
            )
        except SNP.DoesNotExist:
            return None

    def calculate_similarity_to_each_sample(self, alleles: Tuple[str]):
        from .utils import get_genotype
        variants_with_snp = Variant.objects.filter(snp=self).select_related("sample")
        all_samples = {sample.cypher for sample in Sample.objects.all()}
        checked_samples = set()

        similarities: Dict[str, float] = {}

        for variant in variants_with_snp:
            sample = variant.sample.cypher
            if all(allele is None for allele in alleles):
                similarity = 0
            else:
                genotype = get_genotype(*alleles)
                similarity = variant.calculate_similarity(genotype)

            similarities[sample] = similarity
            checked_samples.add(sample)

        for sample_without_variant in all_samples - checked_samples:
            similarities[sample_without_variant] = 0

        return similarities


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
            genotype = f"{alleles[0]}, {alleles[0]}"
        else:
            genotype = ", ".join(str(allele) for allele in alleles) or "unknown"
        return genotype

    def __str__(self):
        return (
            f"Sample: {self.sample}, SNP: {self.snp}, genotype: {self.alleles_record} "
            f"({self.get_genotype_string()})"
        )

    def calculate_similarity(
        self, alleles: Tuple[Allele], metric=identity_percentage
    ) -> float:
        variant_alleles = self.alleles.all()

        if all(allele is None for allele in variant_alleles):
            return 0

        return metric(variant_alleles, alleles)
