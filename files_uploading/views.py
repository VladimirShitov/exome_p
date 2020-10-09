from django.http import HttpResponse
from django.shortcuts import render
from loguru import logger

from .forms import VCFFileForm


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
            return HttpResponse('Something went wrong...')

    else:
        form = VCFFileForm()

    return render(request, 'upload.html', {'form': form})
