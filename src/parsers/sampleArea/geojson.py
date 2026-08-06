#!/usr/bin/env python3
"""
geojson.py

Defines the :class:`Geojson`, which reads a GeoJSON
file and parses it into a :class:`~.datatypes.SampleArea`.
"""

import json
from typing import override, Any

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

    def parse_sample_area(self, json_data: [Any]) -> dt.SampleArea:
        """
        Extract the sample area data from parsed GeoJSON data.

        :param json_data: The raw GeoJSON data to extract
            the sample area from.
        :type json_data: list[Any]

        :param sample_area_padding: Amount to shrink the sample border by.
        :type sample_area_padding: int

        :returns: The extracted sample area.
        :rtype: ~.datatypes.SampleArea
        """

        sample_area: dt.SampleArea | None = None

        for annotation in json_data["features"]:
            try:
                if (
                    annotation["properties"]["classification"]["name"]
                    == "cell_segmentation_sample_area"
                ):
                    area_points = annotation["geometry"]["coordinates"][0]

                    padding: int = self.sample_area_padding

                    tl = area_points[0]
                    br = area_points[2]
                    tr = area_points[3]

                    sample_area = dt.SampleArea(
                        int(tr[0] - padding),
                        int(tl[0] + padding),
                        int(br[1] - padding),
                        int(tr[1] + padding),
                    )

            except KeyError:
                continue

        if sample_area is None:
            raise ValueError("Failed to parse sample area.")

        return sample_area

    @override
    def parse(self, filepath: str) -> dt.SampleArea:
        """
        Read and parse the sample area from a GeoJSON file.

        Reads the file at ``filepath`` and delegates it to
        :meth:`parse_sample_area` to extract the sample area bounds.

        :param filepath: The path to the GeoJSON file.
        :type filepath: str

        :returns: The parsed sample area.
        :rtype: ~.datatypes.SampleArea
        """

        json_data: list[Any] = []
        with open(filepath, "r") as f:
            json_data = json.load(f)

        return self.parse_sample_area(json_data)
