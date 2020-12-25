from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, TypedDict, cast

from django.utils.translation import gettext_lazy as _

from .models import Sample

SamplesDict = Dict[str, Sample]

VariantSimilarity = namedtuple(
    "VariantSimilarity", ["sample", "genotype", "similarity"]
)


class Nucleotide(Enum):
    A = "A"
    T = "T"
    G = "G"
    C = "C"


class VariantDict(TypedDict):
    chromosome: str
    position: int
    allele_1: Nucleotide
    allele_2: Nucleotide


class Table:
    def __init__(self, header: Tuple[str], content: List[tuple]):
        self.header = header
        self.content = content

    def __bool__(self):
        return bool(self.content)


class GenotypesSimilarityTable(Table):
    header = cast(Tuple[str], (_("Sample"), _("Genotype"), _("Similarity")))

    def __init__(self, content: List[VariantSimilarity]):
        super().__init__(header=self.header, content=content)


class SamplesSimilarityTable(Table):
    header = cast(Tuple[str], (_("Sample"), _("Similarity")))

    def __init__(self, content: List[tuple]):
        super().__init__(header=self.header, content=content)


@dataclass
class SNPSearchResult:
    snp_query: VariantDict
    similarity_table: GenotypesSimilarityTable


@dataclass
class SamplesSearchResult:
    samples: SamplesSimilarityTable
    snp_queries: List[SNPSearchResult]


class SampleStatistics(TypedDict):
    n_refs: int
    n_alts: int
    n_missing: int
    has_name_collision: bool
