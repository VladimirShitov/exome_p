from pathlib import Path
import tempfile
from typing import Dict

from django.contrib.staticfiles import finders
from loguru import logger

from files_uploading.vcf_processing import VCFFile
from nationality_prediction.command_line_tools import run_fastngsadmix, run_plink
from nationality_prediction.constants import FAST_NGS_ADMIX_OUTPUT, VCF_FILENAME


class FastNGSAdmixPredictor:
    number_of_individuals_file = finders.find("nInd_humanOrigins_7worldPops.txt")
    reference_panel_file = finders.find("refPanel_humanOrigins_7worldPops.txt")

    def __init__(self, vcf: VCFFile):
        self.vcf = vcf

    def predict(self) -> Dict[str, float]:
        """Predict nationalities from `self.vcf`

        Pipeline for the prediction contains following steps:
        1. Run plink to make .bed file from VCF
        2. Run fastNGSadmix to get .qopt file
        3. Process fastNGSadmix result

        :return: dictionary, where keys are nationalities and values are their probabilities
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)

            logger.info("Saving VCF")
            self.vcf.save(Path(tmp_dir) / VCF_FILENAME)

            run_plink(tmp_dir_path)
            run_fastngsadmix(
                tmp_dir_path,
                number_of_individuals_file=self.number_of_individuals_file,
                ref_panel=self.reference_panel_file
            )

            predicted_nationalities: Dict[str, float] = self.process_fastngsadmix_output(
                tmp_dir_path / FAST_NGS_ADMIX_OUTPUT
            )

            return predicted_nationalities

    @staticmethod
    def process_fastngsadmix_output(filepath: Path) -> Dict[str, float]:
        """Read fastNGSadmix output file and convert it to a python object

        :param filepath: path to fastNGSadmix output with '.qopt' extension
        :return: dictionary, where keys are nationalities and values are their probabilities
        """
        logger.info("Reading fastNGSadmix output")

        with open(filepath) as f:
            predicted_nationalities = f.read()
            logger.debug("Predicted nationalities:\n{}", predicted_nationalities)

        file_content = predicted_nationalities.strip().split('\n')
        nationalities = file_content[0].strip().split()
        scores = file_content[1].strip().split()

        if len(nationalities) != len(scores):
            logger.warning("Nationalities and scores have different length")

        prediction = dict(zip(nationalities, map(float, scores)))

        return prediction

