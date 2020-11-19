from collections import defaultdict
from operator import itemgetter
from typing import Dict, List, Optional, Tuple

from django.http import QueryDict
from loguru import logger
from pysam import VariantRecord

from .models import (SNP, Allele, AllelesRecord, Chromosome, RawVCF, Sample,
                     Variant)
from .types import (SamplesDict, SamplesSearchResult, SamplesSimilarityTable,
                    SNPSearchResult, VariantDict, VariantSimilarity)


def are_samples_empty(record: VariantRecord) -> bool:
    if not record.samples.items():
        logger.warning("No samples detected")
        logger.info("Finishing reading the file")
        return True
    return False


def parse_samples(record: VariantRecord, vcf_file: RawVCF) -> Optional[SamplesDict]:
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
                "Sample {} already exists in the database. Ignoring", sample_name
            )

    return samples


def create_snp(
    chromosome: Chromosome, record: VariantRecord, ref: Allele, alt: Allele
) -> SNP:
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
            variant.alleles.add(Allele.from_str(allele or "."))


def is_record_incomplete(record: VariantRecord) -> bool:
    """Check if `record` is missing a required field: e.g chromosome, alleles or position"""
    return any(
        field is None or not field
        for field in (record.chrom, record.alts, record.ref, record.pos)
    )


def save_record_to_db(record: VariantRecord, samples: SamplesDict):
    if is_record_incomplete(record):
        return

    chromosome: Chromosome = Chromosome.from_record(record)
    reference_allele: Allele = Allele.ref_from_record(record)
    alternative_allele: Allele = Allele.alt_from_record(record)
    snp: SNP = create_snp(
        chromosome=chromosome,
        record=record,
        alt=alternative_allele,
        ref=reference_allele,
    )
    create_variants_from_record(record=record, snp=snp, samples=samples)


def get_genotype(allele_1: str, allele_2: str) -> Tuple[Allele]:
    return Allele.objects.get(genotype=allele_1), Allele.objects.get(genotype=allele_2)


def get_similar_samples_from_snp(snps_formset) -> SamplesSearchResult:
    similar_samples: Dict[str, float]
    results: List[SNPSearchResult] = []
    samples_similarity: Dict[str, float] = defaultdict(float)

    for snp_form in snps_formset:

        genotype: Tuple[Allele] = get_genotype(
            snp_form["allele_1"].data, snp_form["allele_2"].data
        )

        snps = SNP.objects.filter(
            chromosome=snp_form["chromosome"].data,
            position=snp_form["position"].data,
        )

        snp_search_results: List[VariantSimilarity] = []

        for snp in snps:
            variants = Variant.objects.filter(snp=snp).select_related("sample")
            for variant in variants:
                similarity = variant.calculate_similarity(genotype)
                if similarity > 0:
                    sample = str(variant.sample)
                    samples_similarity[sample] += similarity
                    snp_search_results.append(
                        VariantSimilarity(
                            sample=sample,
                            genotype=variant.get_genotype_string(),
                            similarity=similarity,
                        )
                    )

        snp_search_results.sort(key=itemgetter(2), reverse=True)

        samples = SamplesSimilarityTable(content=snp_search_results)
        snp_query = get_snp_from_snp_search_form(snp_form)

        snp_search_result = SNPSearchResult(
            snp_query=snp_query, similarity_table=samples
        )
        results.append(snp_search_result)

    for sample in samples_similarity.keys():
        samples_similarity[sample] = round(
            samples_similarity[sample] /len(results), 4
        )

    search_result = SamplesSearchResult(samples=dict(samples_similarity), snp_queries=results)

    return search_result


def get_snp_from_snp_search_form(request_dict: QueryDict) -> VariantDict:
    snp_dict = {
        "chromosome": Chromosome.NamesMapper.number_to_name(
            int(request_dict["chromosome"].data)
        ),
        "position": request_dict["position"].data,
        "allele_1": request_dict["allele_1"].data,
        "allele_2": request_dict["allele_2"].data,
    }

    return snp_dict
