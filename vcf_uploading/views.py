from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import render
from loguru import logger

from .forms import SNPSearchForm, VCFFileForm
from .models import RawVCF, Sample
from .types import SamplesSearchResult
from .utils import get_similar_samples_from_snp


def index(request):
    return render(request, "base.html")


def vcf_file_upload(
        request,
        form_class=VCFFileForm,
        form_template="upload.html",
        result_template="vcf_summary.html"
):
    if request.method == "POST":
        logger.info("{} received a POST request", vcf_file_upload.__name__)
        form = form_class(request.POST, request.FILES)
        logger.debug("REQUEST.FILES: {}", request.FILES)

        if form.is_valid():
            logger.info("Form is valid, trying to calculate statistics")
            vcf = RawVCF(file=form.cleaned_data["file"])
            vcf.save()
            vcf.calculate_statistics()

            logger.success("Saved the file, returning success")
            return render(request, result_template, {"vcf": vcf})
        else:
            logger.warning("Something has failed")
            logger.debug("Form errors: {}", form.errors)
            return render(request, form_template, {"form": form})

    else:
        form = form_class()

    return render(request, form_template, {"form": form})


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
