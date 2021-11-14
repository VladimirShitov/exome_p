from django.core.validators import FileExtensionValidator
from django.db import models
import pandas as pd


class Sample(models.Model):
    cypher = models.CharField(max_length=255, primary_key=True)


class STRRegion(models.Model):
    title = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.title


class ShortTandemRepeat(models.Model):
    sample = models.ForeignKey(to=Sample, on_delete=models.CASCADE)
    region = models.ForeignKey(to=STRRegion, on_delete=models.CASCADE)
    n_repeats = models.IntegerField()


class STRFile(models.Model):
    file = models.FileField(
        upload_to="raw_data/str/",
        validators=[FileExtensionValidator(allowed_extensions=["xlsx"])]
    )

    def save_to_db(self):
        df = pd.read_excel(self.file.path, engine="openpyxl")

        for region in df.columns[1:]:
            db_record, _ = STRRegion.objects.get_or_create(title=region)
            db_record.save()
