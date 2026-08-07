#!/usr/bin/env python3
"""
geojson.py

Defines the :class:`Geojson`, which reads a GeoJSON file and
parses it into a list of :class:`~.datatypes.Point` objects.
"""

import json

import shapely

from typing import override, Any

import src.datatypes as dt
from src.parsers.parser import Parser


class Geojson(Parser[list[dt.Point]]):
    """
    Parse point objects from a QuPath exported GeoJSON file.

    Reads a GeoJSON file containing manually placed point annotation
    objects and builds a :class:`~.datatypes.Point` object for each point.
    """

    def extract_points(self, geometries: shapely.GeometryCollection) -> list[dt.Point]:
        """
        Extract point objects from geometry collection.

        Finds all points within the ``geometries`` object and
        converts each one to a :class:`~.datatypes.Point` object.

        :param geometries: The geometry collection to extract points from.
        :type geometries: GeometryCollection

        :returns: A list of point objects extracted from the geometry collection.
        :rtype: list[~.datatypes.Point]
        """
        points: list[dt.Point] = []

        for geometry in geometries.geoms:
            if isinstance(geometry, shapely.MultiPoint):
                point_geometries: shapely.MultiPoint = geometry
                for point in point_geometries.geoms:
                    point_x = int(point.x)
                    point_y = int(point.y)

                    point_obj: dt.Point = dt.Point(point_x, point_y)
                    points.append(point_obj)

            elif isinstance(geometry, shapely.Point):
                point: shapely.Point = geometry

                point_x = int(point.x)
                point_y = int(point.y)

                point_obj: dt.Point = dt.Point(point_x, point_y)
                points.append(point_obj)

        return points

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

        # Read in raw data from file
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

        points: list[dt.Point] = self.extract_points(geometries)
        return points
