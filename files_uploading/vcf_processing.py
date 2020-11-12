from pathlib import Path
from typing import List


class VCFRecord:
    def __init__(
            self,
            chromosome,
            position,
            sample,
            sample_indexes,
            ref,
            alts: List[str],
            id_=".",
            quality=".",
            filter_=".",
            format_='.',
            info=".",
    ):
        self.chromosome = chromosome
        self.position = position
        self.id_ = id_
        self.ref = ref
        self.alts = alts
        self.quality = quality
        self.filter_ = filter_
        self.info = info
        self.format_ = format_
        self.sample_indexes = sample_indexes
        self.sample = sample

    def __str__(self):
        return f'{self.chromosome}\t{self.position}\t{self.id_}\t{self.ref}' \
               f'\t{",".join(self.alts)}\t{self.quality}\t{self.filter_}' \
               f'\t{self.info}\t{self.format_}\t{self.sample_indexes}'


class VCFFile:
    header = (
        '##fileformat=VCFv4.3',
        '##source=exome_p',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">'
    )
    columns = ('#CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO', 'FORMAT')

    def __init__(self, sample):
        self.columns_string = '\t'.join(self.columns) + '\t' + sample
        self.records = []

    def add_record(self, record: VCFRecord):
        self.records.append(record)

    def save(self, file_path: Path):
        with open(file_path, 'w') as f:
            f.write('\n'.join(self.header) + '\n')
            f.write(self.columns_string + '\n')
            for record in self.records:
                f.write(str(record) + '\n')
