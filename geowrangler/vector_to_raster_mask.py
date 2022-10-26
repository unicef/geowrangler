# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks/10_vector_to_raster_mask.ipynb (unless otherwise specified).

__all__ = ["generate_mask", "GRID_ID"]


# Cell
import json
from typing import Any, Dict

import geopandas as gpd
import matplotlib.pyplot as plt
import rasterio as rio
import rasterio.mask

# Internal Cell
def _explode(gdf):
    """
    Explodes a geodataframe
    Source: https://gist.github.com/mhweber/cf36bb4e09df9deee5eb54dc6be74d26
    Will explode muti-part geometries into single geometries.
    Args:
        gdf (gpd.GeoDataFrame) : Input geodataframe with multi-geometries
    Returns:
        gdf (gpd.GeoDataFrame) : Exploded geodataframe with a new index
                                 and two new columns: level_0 and level_1
    """

    gs = gdf.explode()
    gdf2 = gs.reset_index().rename(columns={0: "geometry"})
    if "class" in gdf2.columns:
        gdf2 = gdf2.drop("class", axis=1)
    gdf_out = gdf2.merge(
        gdf.drop("geometry", axis=1), left_on="level_0", right_index=True
    )
    gdf_out = gdf_out.set_index(["level_0", "level_1"]).set_geometry("geometry")
    gdf_out.crs = gdf.crs

    return gdf_out


# Cell

GRID_ID = 1


def generate_mask(
    tiff_file,
    shape_file,
    output_file,
    labels_column,
    labels_dict: Dict[str, Any],
    plot=False,
):
    """Generates a segmentation mask for one TIFF image.
    Arguments:
        tiff_file (str): Path to reference TIFF file ||
        shape_file (str): Path to shapefile ||
        output_file (str): Path to output file ||
        labels_column (str): Feature in the shapefile that contains labels/categories ||
        labels_dict (dict): Dictionary of desired labels and assigned values for the mask ||
    Returns:
        image (np.array): A binary mask as a numpy array
    """
    global GRID_ID

    src = rio.open(tiff_file)
    raw = gpd.read_file(shape_file).dropna()
    gdf = _explode(raw)

    label_values = {}

    labels_column = f"{labels_column}_x"

    if labels_column in gdf.columns:
        for keys, values in labels_dict.items():
            label_values[keys] = values

    masks, grids = [], []
    for index, (idx, x) in enumerate(gdf.iterrows()):

        if labels_column in x:
            value = label_values[x[labels_column]]

        gdf_json = json.loads(gpd.GeoDataFrame(x).T.to_json())
        feature = [gdf_json["features"][0]["geometry"]][0]
        masks.append((feature, value))
        grids.append((feature, GRID_ID))
        GRID_ID += 1

    masks = rio.features.rasterize(
        ((g, v) for (g, v) in masks),
        out_shape=src.shape,
        transform=src.transform,
    ).astype(rio.uint16)

    grids = rio.features.rasterize(
        ((g, v) for (g, v) in grids),
        out_shape=src.shape,
        transform=src.transform,
    ).astype(rio.uint16)

    out_meta = src.meta.copy()
    out_meta["count"] = 2
    out_meta["nodata"] = 0
    out_meta["dtype"] = rio.uint16
    out_meta["compress"] = "deflate"

    with rio.open(output_file, "w", **out_meta) as dst:
        dst.write(masks, indexes=1)
        dst.write(grids, indexes=2)

    if plot:
        f, ax = plt.subplots(1, 3, figsize=(15, 15))
        gdf.plot(ax=ax[0])
        rio.plot.show(src, ax=ax[1], adjust=None)
        rio.plot.show(masks, ax=ax[2], adjust=None)

        ax[0].set_title("Vector File")
        ax[1].set_title("TIFF")
        ax[2].set_title("Masked")
        plt.show()

    return masks, grids, label_values
