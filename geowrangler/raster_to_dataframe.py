# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks/11_raster_to_dataframe.ipynb (unless otherwise specified).

__all__ = ["read_bands"]


# Cell
import pandas as pd
import rasterio as rio
import rasterio.mask

# Cell
def read_bands(image_list: [], mask: str):
    """
    Reads the bands for each image in the list and returns a dataframe where each band is one column with the image name as a suffix for column name.
    """

    data = []

    label_ = rio.open(mask)
    label = label_.read(1).ravel()

    # Iterate over each year
    for idx, image_file in enumerate(image_list):
        # Read each band
        subdata = dict()
        raster = rio.open(image_file)

        for band_idx in range(raster.count):
            band = raster.read(band_idx + 1).ravel()
            subdata["B{}".format(band_idx + 1)] = band

        # Cast to pandas subdataframe
        subdata = pd.DataFrame(subdata).fillna(0)
        subdata.columns = [column + "_" + str(idx) for column in subdata.columns]

        data.append(subdata)
        del subdata

    data = pd.concat(data, axis=1)
    data["label"] = label

    return data
