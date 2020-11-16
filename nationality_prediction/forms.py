from django import forms
from django.utils.translation import gettext_lazy as _
from loguru import logger

from nationality_prediction.predictors import FastNGSAdmixPredictor


class VCFUploadForm(forms.Form):
    vcf_file = forms.FileField(required=True, label=_('VCF file'))

    @staticmethod
    def predict_nationality(vcf_file):
        logger.info("Predicting nationality for file {}", vcf_file)
        logger.debug("Type of file: {}", type(vcf_file))
        logger.debug("dir of file: {}", dir(vcf_file))

        predictor = FastNGSAdmixPredictor(vcf_file)
        return predictor.predict()
