"""exome_p URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from nationality_prediction.views import upload_genotype_for_prediction
from vcf_uploading.views import (
    index,
    samples_list,
    snp_search_form,
    vcf_file_download,
    vcf_file_upload,
    vcf_files_list,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index, name="index"),
    path("file/vcf/", vcf_file_upload, name="upload"),
    path("file/vcf/list", vcf_files_list, name="vcf_list"),
    path("file/vcf/<int:file_id>", vcf_file_download, name="vcf_file"),
    path("vcf/sample/list", samples_list, name="samples_list"),
    path("snp/search", snp_search_form, name="snp_search"),
    path(
        "nationality/predict",
        upload_genotype_for_prediction,
        name="nationality_prediction",
    ),
]
