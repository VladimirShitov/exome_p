from operator import itemgetter

from django.http import QueryDict
from loguru import logger
from pysam import VariantRecord
from typing import List, Optional, Tuple

from .models import Allele, AllelesRecord, Chromosome, Sample, SNP, Variant, VCFFile
from .types import SamplesDict, SamplesSimilarityTable, VariantSimilarity, VariantDict


def are_samples_empty(record: VariantRecord) -> bool:
    if not record.samples.items():
        logger.warning('No samples detected')
        logger.info('Finishing reading the file')
        return True
    return False


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


def create_variants_from_record(record: VariantRecord, snp: SNP, samples: SamplesDict):
    for sample_name, sample in record.samples.items():
        alleles_record: AllelesRecord = AllelesRecord.from_sample(sample)

        sample_db_record = samples[sample_name]
        variant = Variant.objects.create(
            alleles_record=alleles_record, snp=snp, sample=sample_db_record
        )

        for allele in sample.alleles:
            if allele is not None:
                variant.alleles.add(Allele.from_str(allele))


def save_record_to_db(record: VariantRecord, samples:SamplesDict):
    chromosome: Chromosome = Chromosome.from_record(record)
    reference_allele: Allele = Allele.ref_from_record(record)
    alternative_allele: Allele = Allele.alt_from_record(record)
    snp: SNP = create_snp(
        chromosome=chromosome,
        record=record,
        alt=alternative_allele,
        ref=reference_allele
    )
    create_variants_from_record(record=record, snp=snp, samples=samples)


def get_genotype(allele_1: str, allele_2:str) -> Tuple[Allele]:
    return Allele.objects.get(genotype=allele_1), Allele.objects.get(genotype=allele_2)


def get_samples_from_snp(request_dict: QueryDict) -> SamplesSimilarityTable:
    genotype: Tuple[Allele] = get_genotype(request_dict['allele_1'], request_dict['allele_2'])

    snps = SNP.objects.filter(
        chromosome=request_dict['chromosome'],
        position=request_dict['position'],
    )

    weighted_samples: List[VariantSimilarity] = []

    for snp in snps:
        variants = Variant.objects.filter(snp=snp).select_related('sample')
        for variant in variants:
            similarity = variant.calculate_similarity(genotype)
            if similarity > 0:
                weighted_samples.append(
                    VariantSimilarity(
                        sample=variant.sample,
                        genotype=variant.get_genotype_string(),
                        similarity=similarity,
                    )
                )

    weighted_samples.sort(key=itemgetter(2), reverse=True)
    samples = SamplesSimilarityTable(content=weighted_samples)

    return samples


def get_snp_from_snp_search_form(request_dict: QueryDict) -> VariantDict:
    snp_dict = {
        'chromosome': request_dict['chromosome'],
        'position': request_dict['position'],
        'allele_1': request_dict['allele_1'],
        'allele_2': request_dict['allele_2'],
    }

    return snp_dict
