#!/usr/bin/env python3
"""
Main entry point for the cell scoring pipeline.

Discovers mask files under a given directory, pairs them with their
associated point annotation files, runs each sample through a
configurable processing pipeline, and writes results to an output
directory.
"""

import re
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import numpy.typing as npt
from alive_progress import alive_bar
from PIL import Image

import src.datatypes as dt
import src.outputs as outputs
import src.processors as processors
import src.parsers as parsers
import src.file_matcher as file_matcher
from src.outputs.output import Output
from src.processors.processor import Process

# Ordered sequence of processing steps applied to each sample.
PROCESSING_PIPELINE: tuple[Process, ...] = (
    processors.CountPoints(),
    processors.DetectClippingCells(),
    processors.CalculateScore(),
)

# Ordered sequence of output steps run after all processing is complete.
OUTPUT_PIPELINE: tuple[Output, ...] = (
    outputs.ScoresCsv(),
    outputs.Overlay(),
)

def process_sample(
    mask_file: tuple[Path, str],
    annotation_file: tuple[Path, str],
    output_directory: Path,
    sample_area_padding: int,
) -> None:

    # Load data into memory
    mask_file_path: Path = mask_file[0]
    annotation_file_path: Path = annotation_file[0]

    cells: dict[int, dt.Cell] = parsers.cells.Tif().parse(
        str(mask_file_path.absolute())
    )

    annotation_file_extension: str = annotation_file_path.name.split(".")[-1].lower()
    if annotation_file_extension == "geojson":
        annotation_file_parser = parsers.points.Geojson()
    elif annotation_file_extension == "tsv":
        annotation_file_parser = parsers.points.Tsv()
    elif annotation_file_extension == "csv":
        annotation_file_parser = parsers.points.Csv()
    else:
        annotation_file_parser = None

    if annotation_file_parser:
        points: list[dt.Point] = annotation_file_parser.parse(
            str(annotation_file_path.absolute())
        )
    else:
        raise ValueError(f"Unsupported filetype: {annotation_file_extension}")

    mask: npt.NDArray[np.uint16] = np.array(
        Image.open(str(mask_file_path.absolute())), dtype="uint16"
    )

    sample_area: dt.SampleArea = parsers.sampleArea.Geojson(sample_area_padding).parse(
        str(annotation_file_path.absolute())
    )

    image_name: str = annotation_file[1]
    model_name: str = mask_file[1]
    metadata: dt.Metadata = dt.Metadata(
        image_name,
        model_name,
        str(annotation_file_path.absolute()),
        str(mask_file_path.absolute()),
    )

    data: dt.Sample = dt.Sample(metadata, cells, points, mask, sample_area)

    for process in PROCESSING_PIPELINE:
        data = process.run(data)

    for output in OUTPUT_PIPELINE:
        output.run(data, output_directory)


def run(
    root_dir: str,
    output_dir: str | None = None,
    max_workers: int | None = None,
    sample_area_padding: int = 5,
    no_progress: bool = False,
) -> None:
    """
    Discover mask files and run the full processing pipeline.

    Searches ``root_dir`` recursively for ``.tif`` mask files and
    processes each one in parallel. Results are written to ``output_dir``
    if provided, otherwise to a ``Results/`` directory placed alongside
    ``root_dir``.

    :param root_dir: Root directory to search for ``.tif`` mask files.
    :param output_dir: Directory for output files. Defaults to a
        ``Results/`` folder next to ``root_dir``.
    :param max_workers: Maximum number of parallel worker processes.
    :param sample_area_padding: Amount to shrink the sample border by.
    :param no_progress: Disable the progress bar.
    """
    root_path = Path(root_dir)
    output_directory: Path = (
        Path(output_dir) if output_dir else root_path.parent / "Results"
    )

    if not max_workers:
        print("No maximum parallel processor count set. Using number of cpu cores...\n")
        max_workers = os.cpu_count()

    print(f"Workers: {max_workers}")
    print(f"Sample area padding: {sample_area_padding}\n")

    # Discover files
    print("Searching for files...")
    file_associations: dict[tuple[Path, str, str], list[tuple[Path, str]]] = (
        file_matcher.associate_files(root_path)
    )

    for annotations_file in file_associations.keys():
        print(annotations_file[0])
        for mask_file in file_associations[annotations_file]:
            print(f"\t-> {mask_file[0]}")

    # Create processor pool
    with ProcessPoolExecutor(max_workers) as executor:
        futures = []

        for annotation_file in file_associations:
            mask_files: list[tuple[Path, str]] = file_associations[annotation_file]

            for mask_file in mask_files:
                future = executor.submit(
                    process_sample,
                    mask_file,
                    annotation_file,
                    output_directory,
                    sample_area_padding,
                )
                futures.append(future)

        if no_progress:
            print(
                "Status bar disabled. The program is still running in the background..."
            )
            for _ in as_completed(futures):
                pass
        else:
            with alive_bar(len(futures)) as bar:
                for _ in as_completed(futures):
                    bar()
