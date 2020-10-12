from django.http import HttpResponse
from django.shortcuts import render
from loguru import logger

from .forms import VCFFileForm
from .models import VCFFile


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


