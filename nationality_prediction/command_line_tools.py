from pathlib import Path
import subprocess

from loguru import logger

from nationality_prediction.constants import VCF_FILENAME, PLINK_OUTPUT_PREFIX


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
