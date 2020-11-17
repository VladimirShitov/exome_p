from django.test import TestCase

from files_uploading.metrics import identity_percentage
from files_uploading.models import Allele


class MetricsTestCase(TestCase):
    def setUp(self):
        Allele.objects.bulk_create(
            [
                Allele(genotype="A"),
                Allele(genotype="T"),
                Allele(genotype="G"),
                Allele(genotype="C"),
            ]
        )

    def test_identity_percentage_metric(self):
        a = Allele.objects.get(genotype="A")
        t = Allele.objects.get(genotype="T")
        g = Allele.objects.get(genotype="G")
        c = Allele.objects.get(genotype="C")

        self.assertEqual(identity_percentage((c,), (t, c)), 0.5)
        self.assertEqual(identity_percentage((c, t), (t, c)), 1)
        self.assertEqual(identity_percentage((c, t), (c, t)), 1)
        self.assertEqual(identity_percentage((c, t), (a, g)), 0)
        self.assertEqual(identity_percentage((c,), (a, a)), 0)
        self.assertEqual(identity_percentage((g,), (g, g)), 1)
        self.assertEqual(identity_percentage((a, g), (t, a)), 0.5)
        self.assertEqual(identity_percentage((a, g), (a, t)), 0.5)
        self.assertEqual(identity_percentage((c, t), (c, c)), 0.5)
