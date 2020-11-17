from django.shortcuts import render
from loguru import logger

from nationality_prediction.forms import VCFUploadForm


def upload_genotype_for_prediction(
    request,
    form_class=VCFUploadForm,
    form_template="vcf_upload.html",
    result_template="nationality_prediction_result.html",
):
    if request.method == "POST":
        logger.info(
            "{} received a POST request", upload_genotype_for_prediction.__name__
        )
        form = form_class(request.POST, request.FILES)
        logger.debug("REQUEST.FILES: {}", request.FILES)

        if form.is_valid():
            logger.success("Form is valid, trying to predict genotype")
            logger.debug(form)
            vcf_file = form.files["vcf_file"]
            result = form.predict_nationality(vcf_file)
            return render(request, result_template, {"predicted_nationalities": result})
        else:
            logger.warning("Something has failed")
            logger.debug("Form errors: {}", form.errors)
            return render(request, form_template, {"form": form})

    else:
        form = form_class

    return render(request, form_template, {"form": form})
