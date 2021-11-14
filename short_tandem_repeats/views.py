from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory
from loguru import logger
import pandas as pd

from short_tandem_repeats.forms import STRFileForm, STRSearchForm
from short_tandem_repeats.models import STRFile


def str_file_upload(
        request,
        form_class=STRFileForm,
        form_template="short_tandem_repeats/str_upload.html"
):
    logger.info("{} received a {} request", str_file_upload.__name__, request.method)

    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        logger.debug("REQUEST.FILES: {}", request.FILES)

        if form.is_valid():
            logger.info("Form is valid, trying to save the file")
            str_file = form.save()
            str_file.save_to_db()
            logger.debug("STR file: {}", str_file)

            return redirect("str_view", file_id=str_file.pk)

        else:
            logger.warning("Something has failed")
            logger.debug("Form errors: {}", form.errors)
            return render(request, form_template, {"form": form})

    else:
        form = form_class()

    return render(request, form_template, {"form": form})


def str_view(
        request,
        file_id: int,
        result_template="short_tandem_repeats/str_table.html"
):
    logger.info("STR view received a request")

    str_file: STRFile = get_object_or_404(STRFile, pk=file_id)
    logger.debug("Reading file {}", str_file.file.name)

    df = pd.read_excel(str_file.file.path, engine="openpyxl")
    columns = df.columns.tolist()

    logger.success("Returning the page")
    return render(
        request,
        result_template,
        {"columns": columns, "rows": df.iterrows(), "name": str_file.file.name},
    )


def str_search_form(
    request,
    form_class=STRSearchForm,
    form_template="str_search.html",
    result_template="str_search_result.html",
):
    formset_class = formset_factory(form_class)

    if request.method == "POST":
        logger.info("{} received a POST request", str_search_form.__name__)
        formset = formset_class(request.POST)

        if formset.is_valid():
            logger.success("Formset is valid, returning success")
            # samples: SamplesSearchResult = get_similar_samples_from_snp(formset)
            # return render(request, result_template, {"result": samples})

        else:
            logger.warning("Formset is not valid")
            return render(request, form_template, {"formset": formset})
    else:
        formset = formset_class()

    return render(request, form_template, {"formset": formset})
