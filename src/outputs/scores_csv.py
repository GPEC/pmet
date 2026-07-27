#!/usr/bin/env python3
"""
scores_csv.py


Defines the :class:`ScoresCsv` output generator, which writes the
processed results of a sample out to a CSV file.
"""

import csv

from pathlib import Path
from filelock import FileLock

import src.datatypes as dt
from src.outputs.output import Output


class ScoresCsv(Output):
    """
    Generate a CSV report of a sample's results.

    Writes the computed :class:`~.datatypes.Results` for a sample
    out to a CSV file.
    """

    def run(self, data: dt.Sample, output_directory: Path) -> None:
        """
        Write the results of one sample to a CSV file.

        :param data: The sample whose results should be written to
            the CSV file.
        :type data: ~.datatypes.Results

        :param output_directory: The directory to write the
            generated CSV file to.
        :type output_directory: pathlib.Path

        :returns: None. The CSV file is written as a side effect to
            a file within ``output_directory``.
        :rtype: None
        """
        output_directory.mkdir(parents=True, exist_ok=True)

        output_file = output_directory / "accuracy_scores.csv"
        output_row = {
            "ImageName": data.metadata.image_name,
            "PointsFile": data.metadata.points_file,
            "MaskFile": data.metadata.mask_file,
            "ModelName": data.metadata.model_name,
            "FalseNegatives": data.results.false_negative,
            "TruePositives": data.results.true_positive,
            "FalsePositives": data.results.false_positive,
            "Precision": data.results.precision,
            "Recall": data.results.recall,
            "F1": data.results.f1,
        }
        # print(f"Precision: {data.results.precision}")
        # print(f"Recall: {data.results.recall}")
        # print(f"F1: {data.results.f1}")

        flock = FileLock(f"{output_file}.lock")
        with flock:
            file_exists: bool = Path(output_file).exists()

            with open(output_file, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=output_row.keys())

                if not file_exists:
                    writer.writeheader()

                writer.writerow(output_row)
