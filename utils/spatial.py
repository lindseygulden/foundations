"""module to hold utility functions for working with geospatial data"""

# pylint: disable=broad-exception-caught
import os

import geopandas as gpd
import pandas as pd
import pyproj
from shapely.geometry import Point
from typing import Union, List, Tuple
from geopy.distance import geodesic
import numpy as np


def read_shapefile(shp_path, prj_path=None, dbf_path=None):
    """
    Reads a shapefile using geopandas and returns the gdf.
    If present reads a projection file (.prj) and puts it in the gdf
    Optionally reads database/attribute file (.dbf); merges its data into the gdf.

    Args:
        shp_path: Path to the shapefile (.shp)
        prj_path: Path to the projection file (.prj)
        dbf_path: Path to the DBF file (.dbf)
    Returns:
        gdf containing the shapefile data
    """
    try:
        gdf = gpd.read_file(shp_path)

        if prj_path:
            try:
                with open(prj_path, "r", encoding="utf-8") as prj_file:
                    prj_text = prj_file.read()
                    crs = pyproj.CRS.from_wkt(prj_text)
                    gdf.set_crs(crs, inplace=True)
            except Exception as e:
                print(f"Error reading projection file: {e}")

        if dbf_path and os.path.exists(dbf_path):
            try:
                dbf_data = pd.read_fwf(dbf_path)
                gdf = gdf.merge(dbf_data, left_index=True, right_index=True, how="left")
            except Exception as e:
                print(f"Error reading DBF file: {e}")

        return gdf
    except Exception as e:
        print(f"Error reading shapefile: {e}")
        return None


def df_to_gdf(df, lat="latitude", lon="longitude", crs="EPSG:4326"):
    """
    Converts a dataframe into a geodataframe with points defined by lat and lon
    Args:
        df: dataframe containing latitude and longitude columns
        lat: column name for latitude
        lon: column name for longitude
        crs: coordinate system to be used for the gdf
    Returns:
        a gdf with points created from df's latitude and longitude columns
    """

    if lat not in df.columns or lon not in df.columns:
        raise ValueError(f"DataFrame must contain '{lat}' and '{lon}' columns.")

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df[lon], df[lat])])

    # Set the coordinate reference system (CRS) to WGS84
    gdf.set_crs(crs, inplace=True)

    return gdf


def distance_between_points(
    p1: Union[Tuple[float], List[float]],
    p2: Union[Tuple[float], List[float]],
) -> float:
    """computes distance in kilometers between two points (lat,lon) or [lat,lon]"""
    for point in [p1, p2]:
        if not (isinstance(point, list) | isinstance(point, tuple)) | (len(point) != 2):
            raise TypeError("Points must be two-member lists or tuples with lat, lon")
    try:
        distance_km = geodesic(tuple(p1), tuple(p2)).kilometers
        return distance_km
    except:
        np.nan
