#!/usr/bin/env python3
"""
geojson.py

Defines the :class:`Geojson`, which reads a GeoJSON
file and parses it into a :class:`~.datatypes.SampleArea`.
"""

import json

import shapely

from typing import override, Any

from shapely.errors import ShapelyDeprecationWarning

import src.datatypes as dt
from src.parsers.parser import Parser


class Geojson(Parser[dt.SampleArea]):
    """
    Parse sample area bounds from a GeoJSON file.

    Reads a QuPath exported GeoJSON file and extracts the
    sample area bounds into a :class:`~.datatypes.SampleArea`
    instance.
    """

    def __init__(self, sample_area_padding: int):
        self.sample_area_padding: int = sample_area_padding

    def extract_sample_area(self, geometries: shapely.GeometryCollection) -> dt.SampleArea:
        """
        Extract the sample area data from a GeometryCollection.

        :param geometries: The GeometryCollection to
            extract the sample area from.
        :type geometries: shapely.GeometryCollection

        :param sample_area_padding: Amount to shrink the sample border by.
        :type sample_area_padding: int

        :returns: The extracted sample area.
        :rtype: ~.datatypes.SampleArea
        """

        sample_area: dt.SampleArea | None = None

        for geometry in geometries.geoms:
            print(dir(geometry))

        if sample_area is None:
            raise ValueError("Failed to parse sample area.")

        return sample_area

    @override
    def parse(self, filepath: str) -> dt.SampleArea:
        """
        Read and parse the sample area from a GeoJSON file.

        Reads the file at ``filepath`` and delegates it to
        :meth:`extract_sample_area` to extract the sample area bounds.

        :param filepath: The path to the GeoJSON file.
        :type filepath: str

        :returns: The parsed sample area.
        :rtype: ~.datatypes.SampleArea
        """

        raw_json: Any
        with open(filepath, "r") as f:
            raw_json = json.load(f)

        if isinstance(raw_json, dict):
            raw_data = str(raw_json)
        elif isinstance(raw_json, list):
            raw_data = json.dumps({
                "type": "FeatureCollection",
                "features": raw_json,
            })
        else:
            raise TypeError(f"Invalid geojson format in file: {filepath}")

        # Convert raw data to usable objects
        geometries: shapely.GeometryCollection = shapely.GeometryCollection(shapely.from_geojson(raw_data))

        sample_area: dt.SampleArea = self.extract_sample_area(geometries)
        return sample_area
