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
import vcf_uploading.views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", vcf_uploading.views.index, name="index"),
    path("file/vcf/", vcf_uploading.views.vcf_file_upload, name="upload"),
    path("file/vcf/list", vcf_uploading.views.vcf_files_list, name="vcf_list"),
    path("file/vcf/<int:file_id>", vcf_uploading.views.vcf_view, name="vcf_view"),
    path("file/vcf/<int:file_id>/download", vcf_uploading.views.vcf_file_download, name="vcf_file"),
    path("file/vcf/<int:file_id>/save", vcf_uploading.views.save_vcf, name="save_vcf"),
    path(
        "file/vcf/<int:file_id>/nationality",
        vcf_uploading.views.predict_nationality_from_vcf,
        name="predict_nationality_from_vcf"
    ),
    path("vcf/sample/list", vcf_uploading.views.samples_list, name="samples_list"),
    path("snp/search", vcf_uploading.views.snp_search_form, name="snp_search"),
    path(
        "nationality/predict",
        upload_genotype_for_prediction,
        name="nationality_prediction",
    ),
]
