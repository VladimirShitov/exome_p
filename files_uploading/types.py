from collections import namedtuple
from typing import Dict, cast, List, Tuple

from django.utils.translation import gettext_lazy as _

from .models import Sample


SamplesDict = Dict[str, Sample]

VariantSimilarity = namedtuple('VariantSimilarity', ['sample', 'genotype', 'similarity'])


class Table:
    def __init__(self, header: Tuple[str], content: List[tuple]):
        self.header = header
        self.content = content

    def __bool__(self):
        return bool(self.content)


class SamplesSimilarityTable(Table):
    header = cast(Tuple[str], (_('Sample'), _('Genotype'), _('Similarity')))

    def __init__(self, content: List[tuple]):
        super().__init__(header=self.header, content=content)
