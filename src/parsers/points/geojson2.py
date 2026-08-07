#!/usr/bin/env python3
"""
geojson.py

Defines the :class:`Geojson`, which reads a GeoJSON file and
parses it into a list of :class:`~.datatypes.Point` objects.
"""

import json

## TESTING THIS!!
from shapely import Point

from typing import override, Any

import src.datatypes as dt
from src.parsers.parser import Parser


class Geojson2(Parser[list[dt.Point]]):
    """
    Parse point objects from a QuPath exported GeoJSON file.

    Reads a GeoJSON file containing manually placed point annotation
    objects and builds a :class:`~.datatypes.Point` object for each point.
    """

    @override
    def parse(self, filepath: str) -> list[dt.Point]:
        """
        Generate point objects from a QuPath GeoJSON file.

        Reads the GeoJSON file at ``filepath`` and builds a
        :class:`~.datatypes.Point` object for each annotation it contains.

        :param filepath: The path to the GeoJSON file to parse.
        :type filepath: str

        :returns: A list of point objects parsed from the file.
        :rtype: list[~.datatypes.Point]
        """

        points: list[dt.Point] = []

        raw_data: Any
        with open(filepath, "r") as f:
            raw_data = json.load(f)

        print(raw_data.values())

        return points
