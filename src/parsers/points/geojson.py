#!/usr/bin/env python3
"""
geojson.py

Defines the :class:`Geojson`, which reads a GeoJSON file and
parses it into a list of :class:`~.datatypes.Point` objects.
"""

import json
from typing import override, Any

import src.datatypes as dt
from src.parsers.parser import Parser


class Geojson(Parser[list[dt.Point]]):
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

        json_data: list[Any] = []
        with open(filepath, "r") as f:
            json_data = json.load(f)

        if json_data["type"] == "FeatureCollection":
            json_data = json_data["features"]
            for feature in json_data:
                if feature["geometry"]["type"] == "Point":
                    point_entry = feature["geometry"]["coordinates"]
                    point_x: int = int(point_entry[0])
                    point_y: int = int(point_entry[1])

                    point: dt.Point = dt.Point(point_x, point_y)

                    points.append(point)

        else:
            print(f"VALUES (kill me) {json_data.values()}")
            for feature in json_data:
                if feature["geometry"]["type"] == "MultiPoint" or feature["geometry"]["type"] == "Point":
                    print("Got a point match!")
                    for point_entry in feature["geometry"]["coordinates"]:
                        point_x: int = int(point_entry[0])
                        point_y: int = int(point_entry[1])

                        point: dt.Point = dt.Point(point_x, point_y)

                        points.append(point)

        return points
