# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/12_spatialjoin_highest_intersection.ipynb.

# %% auto 0
__all__ = ['get_highest_intersection']

# %% ../notebooks/12_spatialjoin_highest_intersection.ipynb 6
import json
import os
import geopandas as gpd
import pandas as pd
import requests
from . import grids

# %% ../notebooks/12_spatialjoin_highest_intersection.ipynb 23
def get_highest_intersection(
    gdf1: gpd.GeoDataFrame,  # gdf1 will be the basis of output geometry
    gdf2: gpd.GeoDataFrame,  # gdf2 data will all be included during intersection
    proj_crs: str,  # metric CRS (e.g., Philippines uses EPSG:32651)
) -> gpd.GeoDataFrame:
    """Gets the intersection based on the largest area joined"""

    gdf1 = gdf1.copy()
    gdf2 = gdf2.copy()

    # renaming columns with __ prefixes and suffixes so they're less likely to be already used
    uid_col = "__uid__"
    area_col = "__area_highest_intersection__"
    auxiliary_cols = [uid_col, area_col]

    # checks to make sure we're not overwriting existing oclumns
    for col in auxiliary_cols:
        if col in gdf1.columns:
            raise ValueError(f"Make sure {col} isn't already a column in gdf1")
        if col in gdf2.columns:
            raise ValueError(f"Make sure {col} isn't already a column in gdf2")

    # assign uid to gdf1
    gdf1[uid_col] = range(len(gdf1))  # assign uid based on row number of first gdf

    # get intersection of the gdfs
    overlay = gdf1.overlay(gdf2, how="intersection")

    # add relevant columns
    overlay["geometry"] = overlay["geometry"].to_crs(
        proj_crs
    )  # geometry produced will be based on gdf1
    overlay[area_col] = (
        overlay.geometry.area
    )  # shows area of overlap, not the area of the polygon in gdf1

    # sorting of values, dropping duplicates and null values
    overlay = overlay.sort_values(by=area_col, ascending=True)
    overlay = overlay.drop_duplicates(subset=[uid_col], keep="last")
    overlay = overlay.dropna(
        subset=[uid_col]
    )  # drops rows with value in gdf2 but has no info in gdf1
    assert not overlay[uid_col].duplicated().any()
    overlay = overlay.sort_values(by=[uid_col], ascending=True)

    # drop geometry from overlay gdf
    overlay_merge = overlay.drop(
        "geometry", axis=1
    )  # two geometries will be produced, drop overlay geometry

    output = pd.merge(
        left=gdf1[[uid_col, "geometry"]],
        right=overlay_merge,
        on=uid_col,
        how="left",
        validate="one_to_one",
    )

    output = output.drop(columns=auxiliary_cols)

    return output
