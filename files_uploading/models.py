from django.db import models


class VCFFile(models.Model):
    file = models.FileField()
