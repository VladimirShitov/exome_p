import tempfile
from pathlib import Path
from typing import Dict, Union

from django.contrib.staticfiles import finders
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _
from loguru import logger
from pysam import VariantFile

from nationality_prediction.command_line_tools import run_fastngsadmix, run_plink
from nationality_prediction.constants import FAST_NGS_ADMIX_OUTPUT, VCF_FILENAME
from vcf_uploading.vcf_processing import VCFFile


class FastNGSAdmixPredictor:
    number_of_individuals_file = finders.find("nInd_humanOrigins_7worldPops.txt")
    reference_panel_file = finders.find("refPanel_humanOrigins_7worldPops.txt")

    def __init__(self, vcf: Union[VCFFile, InMemoryUploadedFile, VariantFile]):
        self.vcf = vcf

    def predict(self) -> Dict[str, float]:
        """Predict nationalities from `self.vcf`

        This function does the following steps:
        1. Create temporary directory
        2. Save `self.vcf` file
        3. Run command line tools with `self.run_command_line_tools()`
        4. Return result of the prediction

        :return: dictionary, where keys are nationalities and values are their probabilities
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            vcf_file_path = tmp_dir_path / VCF_FILENAME

            logger.info("Saving VCF")
            if isinstance(self.vcf, VCFFile):
                logger.info("Received VCFFile")
                self.vcf.save(vcf_file_path)
                predicted_nationalities = self.run_command_line_tools(tmp_dir_path)

            elif isinstance(self.vcf, InMemoryUploadedFile):
                logger.info("Received InMemoryUploadedFile")
                with open(vcf_file_path, "w") as f:
                    f.write(self.vcf.read().decode())
                    predicted_nationalities = self.run_command_line_tools(tmp_dir_path)

            elif isinstance(self.vcf, VariantFile):
                logger.info("Received VariantFile")
                with open(vcf_file_path, "w") as temp_vcf:
                    temp_vcf.write(str(self.vcf.header))
                    for record in self.vcf.fetch():
                        temp_vcf.write(str(record))

                    predicted_nationalities = self.run_command_line_tools(tmp_dir_path)
                    logger.debug("Last record: {}", str(record))

            else:
                raise ValueError(
                    _(f"Type {type(self.vcf)} is not supported for VCF files")
                )

            return predicted_nationalities

    def run_command_line_tools(self, directory: Path) -> Dict[str, float]:
        """Predict nationality for VCF-file in the`directory`

        :param directory: directory, which contains VCF file named `constants.VCF_FILENAME`

        Pipeline for the prediction contains following steps:
        1. Run plink to make .bed file from VCF
        2. Run fastNGSadmix to get .qopt file
        3. Process fastNGSadmix result and return it as a Python dictionary

        :return: dictionary, where keys are nationalities and values are their probabilities
        """
        run_plink(directory)
        run_fastngsadmix(
            directory,
            number_of_individuals_file=self.number_of_individuals_file,
            ref_panel=self.reference_panel_file,
        )

        predicted_nationalities: Dict[str, float] = self.process_fastngsadmix_output(
            directory / FAST_NGS_ADMIX_OUTPUT
        )

        return predicted_nationalities

    @staticmethod
    def process_fastngsadmix_output(filepath: Path) -> Dict[str, float]:
        """Read fastNGSadmix output file and convert it to a python object

        :param filepath: path to fastNGSadmix output with '.qopt' extension
        :return: dictionary, where keys are nationalities and values are their probabilities
        """
        logger.info("Reading fastNGSadmix output")

        try:
            with open(filepath) as f:
                predicted_nationalities = f.read()
                logger.debug("Predicted nationalities:\n{}", predicted_nationalities)
        except FileNotFoundError:
            return {
                "French": 0,
                "Han": 0,
                "Chukchi": 0,
                "Karitiana": 0,
                "Papuan": 0,
                "Sindhi": 0,
                "Yoruba": 0
            }

        file_content = predicted_nationalities.strip().split("\n")
        nationalities = file_content[0].strip().split()
        scores = file_content[1].strip().split()

        if len(nationalities) != len(scores):
            logger.warning("Nationalities and scores have different length")

        prediction = dict(zip(nationalities, map(float, scores)))

        return prediction
