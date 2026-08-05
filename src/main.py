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


def import_dataset(
    mask_file: Path, root: Path, sample_area_padding: int
) -> list[dt.Sample]:
    """
    Build Sample objects for a single mask file.

    Parses the image and model names from the mask filename, loads cell
    detections and the mask array from that file, then searches ``root``
    recursively for every GeoJSON point annotation file that belongs to
    the same image. One Sample is created per matching GeoJSON file.

    :param mask_file: Path to the mask ``.tif`` file to import.
    :param root: Directory to search for associated GeoJSON annotation files.
    :param sample_area_padding: Amount to shrink the sample border by.
    :return: A list of Sample objects, one per matched annotation file.
    :raises ValueError: If ``mask_file`` does not match the expected naming
        convention.
    """
    jobs: list[dt.Sample] = []

    # Extract the image name and model name from the mask filename.
    mask_file_regex = re.compile(
        r"(?P<image>.+?)\.ome\.tif\s*-\s*Image\d*\s*_?(?P<model>.+?)_label\.tif"
    )
    match = mask_file_regex.search(mask_file.name)

    if not match:
        raise ValueError(
            f"Mask filename does not match expected format: {mask_file.name}"
        )

    image_name = match.group("image")
    model_name = match.group("model")

    # Load cell detection objects and the raw mask array from the mask file.
    cell_objects: dict[int, dt.Cell] = parsers.cells.Tif().parse(
        str(mask_file.absolute())
    )
    mask_array: npt.NDArray[np.uint16] = np.array(
        Image.open(str(mask_file.absolute())), dtype="uint16"
    )

    # Find all GeoJSON annotation files in ``root`` for this image.
    points_file_regex = re.compile(
        rf"^{re.escape(image_name)}\.ome\.tif - Image\d*\.geojson$"
    )
    points_files = [
        p
        for p in root.rglob("*.geojson")
        if p.is_file() and points_file_regex.match(p.name)
    ]

    for points_file in points_files:
        filepath: str = str(points_file.absolute())

        try:
            sample_area: dt.SampleArea = parsers.sampleArea.Geojson(
                sample_area_padding
            ).parse(filepath)
        except ValueError as e:
            print(f"Error: {e} for file {filepath}")
            continue

        points: list[dt.Point] = parsers.points.Geojson().parse(filepath)

        metadata: dt.Metadata = dt.Metadata(
            image_name, model_name, points_file.name, mask_file.name
        )

        jobs.append(
            dt.Sample(
                metadata=metadata,
                cells=cell_objects,
                points=points,
                mask=mask_array,
                sample_area=sample_area,
            )
        )

    return jobs


def process_sample(
    mask_file: tuple[Path, str],
    annotation_file: tuple[Path, str],
    output_directory: Path,
    sample_area_padding: int,
) -> None:

    print(f"Beging processing on {mask_file[0].name}")

    # Load data into memory

    mask_file_path: Path = mask_file[0]
    annotation_file_path: Path = annotation_file[0]

    cells: dict[int, dt.Cell] = parsers.cells.Tif().parse(
        str(mask_file_path.absolute())
    )
    print(f"Loaded cells for {mask_file[0].name}")

    points: list[dt.Point] = parsers.points.Geojson().parse(
        str(annotation_file_path.absolute())
    )
    print(f"Loaded points for {mask_file[0].name}")

    mask: npt.NDArray[np.uint16] = np.array(
        Image.open(str(mask_file_path.absolute())), dtype="uint16"
    )
    print(f"Loaded mask for {mask_file[0].name}")

    sample_area: dt.SampleArea = parsers.sampleArea.Geojson(sample_area_padding).parse(
        str(annotation_file_path.absolute())
    )
    print(f"Loaded sample area for {mask_file[0].name}")

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
    file_associations: dict[tuple[Path, str], list[tuple[Path, str]]] = (
        file_matcher.associate_files(root_path)
    )

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
