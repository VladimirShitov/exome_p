from pathlib import Path
import subprocess

from loguru import logger

from nationality_prediction.constants import (
    FAST_NGS_ADMIX_OUTPUT_PREFIX,
    VCF_FILENAME,
    PLINK_OUTPUT_PREFIX
)


def run_plink(dir_path: Path):
    """Run plink with files in `dir_path`. Save result to the same directory

    :param dir_path: directory, which contains VCF file for prediction. By default, it will
        search for `constants.VCF_FILENAME` and save files in the same directory with prefix
        `constants.PLINK_FILE`
    """
    logger.info("Running plink")

    result = subprocess.run(
        [
            "plink",
            "--vcf", dir_path / VCF_FILENAME,
            "--make-bed",
            "--recode",
            "--out", dir_path / PLINK_OUTPUT_PREFIX
        ],
        capture_output=True
    )
    logger.debug("STDOUT: {}", result.stdout)
    logger.debug("STDERR: {}", result.stderr)


def run_fastngsadmix(dir_path: Path, number_of_individuals_file: str, ref_panel: str):
    """Run fastNGSadmix with files in `dir_path`. Save result to the same directory

    :param dir_path: directory, which contains plink output files. They have to start with
        `constants.PLINK_OUTPUT_PREFIX`
    :param number_of_individuals_file: a file with number of individuals in each
        reference population
    :param ref_panel: a file with ancestral population frequencies
    """
    logger.info("Running fastNGSadmix")
    fast_ngs_admix_result = subprocess.run(
        [
            "fastNGSadmix",
            "-plink", dir_path / PLINK_OUTPUT_PREFIX,
            "-Nname", number_of_individuals_file,
            "-fname", ref_panel,
            "-out", dir_path / FAST_NGS_ADMIX_OUTPUT_PREFIX,
            "-whichPops", "all",
        ],
        capture_output=True
    )
    logger.debug("STDOUT: {}", fast_ngs_admix_result.stdout)
    logger.debug("STDERR: {}", fast_ngs_admix_result.stderr)
