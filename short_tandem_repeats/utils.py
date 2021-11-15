from django.core.exceptions import ObjectDoesNotExist
from loguru import logger

from short_tandem_repeats.models import Sample, ShortTandemRepeat, NRepeats, STRRegion


def find_sample(strs_formset):
    similar_samples = []

    for str_form in strs_formset:
        str_region = str_form["region"].value()
        n_repeats = str_form["n_repeats"].value()

        logger.debug("Region: {}", str_region)
        logger.debug("N repeats: {}", n_repeats)

        try:
            db_region = STRRegion.objects.get(title=str_region)
        except ObjectDoesNotExist:
            continue

        try:
            db_n_repeats = NRepeats.objects.get(n_repeats=n_repeats)
        except ObjectDoesNotExist:
            continue

        try:
            db_strs = ShortTandemRepeat.objects.filter(n_repeats=db_n_repeats, region=db_region)
            similar_samples.extend([repeat.sample.cypher for repeat in db_strs])
        except ObjectDoesNotExist:
            continue

    return similar_samples
