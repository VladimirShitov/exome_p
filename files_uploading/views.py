from django.http import HttpResponse
from django.shortcuts import render
from loguru import logger

from .forms import VCFFileForm, SNPSearchForm
from .models import VCFFile, Sample
from .utils import get_samples_from_snp, get_snp_from_snp_search_form
from .types import VariantDict, SamplesSimilarityTable


def index(request):
    return render(request, 'base.html')


def vcf_file_upload(request):
    if request.method == 'POST':
        logger.info('{} received a POST request', vcf_file_upload.__name__)
        form = VCFFileForm(request.POST, request.FILES)
        logger.debug('REQUEST.FILES: {}', request.FILES)

        if form.is_valid():
            logger.info('Form is valid, trying to save the file')
            form.save()
            logger.success('Saved the file, returning success')
            return HttpResponse('Yay! You uploaded the file')
        else:
            logger.warning('Something has wailed')
            logger.debug('Form errors: {}', form.errors)
            return render(request, 'upload.html', {'form': form})

    else:
        form = VCFFileForm()

    return render(request, 'upload.html', {'form': form})


def vcf_files_list(request):
    files = VCFFile.objects.all()
    return render(request, 'vcf_list.html', {'files': files})


def vcf_file_download(request, file_id: int):
    file_object: VCFFile = VCFFile.objects.get(pk=file_id)
    file = file_object.file

    response = HttpResponse(file.read(), content_type="text/plain")
    response['Content-Disposition'] = f'attachment; filename={file.name}'

    return response


def samples_list(request):
    samples = Sample.objects.all()
    return render(request, 'samples_list.html', {'samples': samples})


def snp_search_form(
        request,
        form_class=SNPSearchForm,
        form_template='snp_search.html',
        result_template='table_viewer.html',
):
    if request.method == 'POST':
        logger.info('{} received a POST request', snp_search_form.__name__)
        form = form_class(request.POST)
        if form.is_valid():
            logger.success('Form is valid, returning success')
            samples: SamplesSimilarityTable = get_samples_from_snp(request.POST)
            snp_description: VariantDict = get_snp_from_snp_search_form(request.POST)
            return render(
                request, result_template, {'table': samples, 'description': snp_description}
            )
        else:
            logger.warning('Form is not valid')
            return render(request, form_template, {'form': form})
    else:
        form = form_class

    return render(request, form_template, {'form': form})
