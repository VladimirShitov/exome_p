from typing import Dict

from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from loguru import logger

from .forms import SNPSearchForm, VCFFileForm
from .models import RawVCF, Sample
from .types import SamplesSearchResult, SamplesStatisticsTable, SampleStatistics
from .utils import get_similar_samples_from_snp


def index(request):
    return render(request, "base.html")


def vcf_file_upload(
    request,
    form_class=VCFFileForm,
    form_template="upload.html"
):
    if request.method == "POST":
        logger.info("{} received a POST request", vcf_file_upload.__name__)
        form = form_class(request.POST, request.FILES)
        logger.debug("REQUEST.FILES: {}", request.FILES)

        if form.is_valid():
            logger.info("Form is valid, trying to calculate statistics")
            vcf = RawVCF(file=form.cleaned_data["file"])
            vcf.saved = False
            vcf.save()  # Save information, that a file is not saved, LOL

            return redirect("vcf_view", file_id=vcf.pk)
        else:
            logger.warning("Something has failed")
            logger.debug("Form errors: {}", form.errors)
            return render(request, form_template, {"form": form})

    else:
        form = form_class()

    return render(request, form_template, {"form": form})


def vcf_view(
        request,
        file_id: int,
        result_template="vcf_summary.html"
):
    logger.info("VCF view received a request")

    vcf: RawVCF = get_object_or_404(RawVCF, pk=file_id)
    samples_statistics_table = SamplesStatisticsTable.from_dict(
        vcf.calculate_statistics()
    )
    logger.debug("VCF is saved? {}", vcf.saved)

    logger.success("Calculated statistics, returning the page")
    return render(
        request,
        result_template,
        {"vcf": vcf, "samples_statistics_table": samples_statistics_table},
    )


def vcf_files_list(request):
    files = RawVCF.objects.all()
    return render(request, "vcf_list.html", {"files": files})


def vcf_file_download(request, file_id: int):
    file_object: RawVCF = RawVCF.objects.get(pk=file_id)
    file = file_object.file

    response = HttpResponse(file.read(), content_type="text/plain")
    response["Content-Disposition"] = f"attachment; filename={file.name}"

    return response


def samples_list(request):
    samples = Sample.objects.all()
    return render(request, "samples_list.html", {"samples": samples})


def snp_search_form(
    request,
    form_class=SNPSearchForm,
    form_template="snp_search.html",
    result_template="snp_search_result.html",
):
    formset_class = formset_factory(form_class)

    if request.method == "POST":
        logger.info("{} received a POST request", snp_search_form.__name__)
        formset = formset_class(request.POST)

        if formset.is_valid():
            logger.success("Formset is valid, returning success")
            samples: SamplesSearchResult = get_similar_samples_from_snp(formset)
            return render(request, result_template, {"result": samples})

        else:
            logger.warning("Formset is not valid")
            return render(request, form_template, {"formset": formset})
    else:
        formset = formset_class()

    return render(request, form_template, {"formset": formset})


def save_vcf(request, file_id: int):
    vcf: RawVCF = get_object_or_404(RawVCF, pk=file_id)
    vcf.save_samples_to_db()
    return redirect("vcf_view", file_id=vcf.pk)


def predict_nationality_from_vcf(
        request,
        file_id: int,
        result_template="nationality_prediction_result.html"
):
    vcf: RawVCF = get_object_or_404(RawVCF, pk=file_id)
    nationalities_prediction: Dict[str, Dict[str, float]] = vcf.predict_nationality()

    return render(
        request,
        result_template,
        {"predicted_nationalities": nationalities_prediction, "multiple_samples": True}
    )


def find_similar_samples_in_db(
        request,
        file_id: int,
        result_template="similar_samples.html"
):
    logger.info("{} receined a request", find_similar_samples_in_db.__name__)
    vcf: RawVCF = get_object_or_404(RawVCF, pk=file_id)
    similar_samples: Dict[str, Dict[str, float]] = vcf.find_similar_samples_in_db()
    return render(request, result_template, {"similar_samples": similar_samples})
