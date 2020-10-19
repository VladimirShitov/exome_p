from django.contrib import admin

from .models import (
    Allele,
    AllelesRecord,
    Chromosome,
    SNP,
    Nationality,
    MitochondriaHaplogroup,
    YHaplogroup,
    Sample,
    Variant,
)


admin.site.register(Allele)
admin.site.register(AllelesRecord)
admin.site.register(Chromosome)
admin.site.register(SNP)
admin.site.register(Nationality)
admin.site.register(MitochondriaHaplogroup)
admin.site.register(YHaplogroup)
admin.site.register(Sample)
admin.site.register(Variant)
