from django.core.validators import FileExtensionValidator
from django.db import models
import pandas as pd
from loguru import logger


class Sample(models.Model):
    cypher = models.CharField(max_length=255, primary_key=True)


class STRRegion(models.Model):
    title = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.title


class NRepeats(models.Model):
    n_repeats = models.CharField(max_length=10, primary_key=True)

    def __str__(self):
        return self.n_repeats


class ShortTandemRepeat(models.Model):
    sample = models.ForeignKey(to=Sample, on_delete=models.CASCADE)
    region = models.ForeignKey(to=STRRegion, on_delete=models.CASCADE)
    n_repeats = models.ForeignKey(to=NRepeats, on_delete=models.SET("-"))


class STRFile(models.Model):
    file = models.FileField(
        upload_to="raw_data/str/",
        validators=[FileExtensionValidator(allowed_extensions=["xlsx"])]
    )

    def save_to_db(self):
        df = pd.read_excel(self.file.path, engine="openpyxl")

        logger.info("Saving df to the database")
        logger.debug("df shape: {}", df.shape)

        for idx, row in df.iterrows():
            logger.debug("Saving row {}", idx)

            db_sample, _ = Sample.objects.get_or_create(cypher=row["Sample"])
            db_sample.save()

            for region in df.columns[1:]:
                db_region, _ = STRRegion.objects.get_or_create(title=region)
                db_region.save()

                db_n_repeats, _ = NRepeats.objects.get_or_create(n_repeats=str(row[region]))

                repeat, _ = ShortTandemRepeat.objects.get_or_create(
                    sample=db_sample, region=db_region, n_repeats=db_n_repeats)
                repeat.save()
