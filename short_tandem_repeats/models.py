from django.core.validators import FileExtensionValidator
from django.db import models


class STRFile(models.Model):
    file = models.FileField(
        upload_to="raw_data/str/",
        validators=[FileExtensionValidator(allowed_extensions=["xlsx"])]
    )


class Sample(models.Model):
    cypher = models.CharField(max_length=255, primary_key=True)


class STRRegion(models.Model):
    title = models.CharField(max_length=255, primary_key=True)


class ShortTandemRepeat(models.Model):
    sample = models.ForeignKey(to=Sample, on_delete=models.CASCADE)
    region = models.ForeignKey(to=STRRegion, on_delete=models.CASCADE)
    n_repeats = models.IntegerField()
