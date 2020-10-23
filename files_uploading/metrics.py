from typing import Tuple

from .models import Allele


def identity_percentage(reference_alleles: Tuple[Allele], alleles: Tuple[Allele]) -> float:
    """Calculate the percentage of alleles that are both in `reference_alleles` and in
    `variant_alleles`

    :param reference_alleles: tuple of alleles of a Variant model. Important note: it can contain
      only one element! E. g. if reference_alleles == ('C', ), than Variant genotype is actually
      ('C', 'C')
    :param alleles: tuple of some alleles for comparison with `reference_alleles` 
    """
    if len(reference_alleles) == 1 and all(allele in reference_alleles for allele in alleles):
        return 1

    common_elements = set(reference_alleles) & set(alleles)

    return len(common_elements) / 2
