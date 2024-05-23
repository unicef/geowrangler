# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/08_tile_clustering.ipynb.

# %% auto 0
__all__ = ['TileClustering']

# %% ../notebooks/08_tile_clustering.ipynb 5
from collections import deque
from typing import List, Optional, Tuple

import pandas as pd
from fastcore.basics import patch

# %% ../notebooks/08_tile_clustering.ipynb 6
class TileClustering:
    """
    Cluster together adjacent square grid cells. Grid cells belonging to the same cluster will get
    assigned the same ID. Optionally, you cluster adjacent cells by category by passing in `category_col`

    By default, with cluster_type = " four-way", it clusters together grid cells with adjacent edges only.
    If you wish to consider grid cells with adjacent corners as well, use cluster_type = " eight-way"
    """

    def __init__(
        self,
        cluster_type: str = "four_way",
    ) -> None:

        assert cluster_type in ["four_way", "eight_way"]
        self.cluster_type = cluster_type
        self.tile_cluster_col = "tile_cluster"

# %% ../notebooks/08_tile_clustering.ipynb 7
@patch
def cluster_tiles(
    self: TileClustering,
    df: pd.DataFrame,
    grid_x_col="x",
    grid_y_col="y",
    category_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Appends the cluster ID for each square grid cell
    """

    if category_col is None:
        cluster_df = self._cluster_tiles_single(df, grid_x_col, grid_y_col)
    else:
        assert (
            not df[category_col].isnull().any()
        ), f"There shouldn't be null values for {category_col}"
        unique_categories = df[category_col].unique().tolist()

        cluster_df_list = []
        for i, category in enumerate(unique_categories, start=1):
            bool_mask = df[category_col] == category
            filtered_df = df.loc[bool_mask, :].copy()
            cluster_filtered_df = self._cluster_tiles_single(
                filtered_df, grid_x_col, grid_y_col
            )
            cluster_filtered_df[self.tile_cluster_col] = cluster_filtered_df[
                self.tile_cluster_col
            ].apply(lambda key: f"{key}-{i}")
            cluster_df_list.append(cluster_filtered_df)
        cluster_df = pd.concat(cluster_df_list, axis=0, ignore_index=True)

    df = pd.merge(left=df, right=cluster_df, on=[grid_x_col, grid_y_col], how="left")

    return df

# %% ../notebooks/08_tile_clustering.ipynb 8
@patch
def _cluster_tiles_single(
    self: TileClustering,
    df: pd.DataFrame,
    grid_x_col="x",
    grid_y_col="y",
) -> pd.DataFrame:
    """
    Performs tile clustering on a single category
    """

    if self.tile_cluster_col in df.columns:
        raise ValueError(
            f"{self.tile_cluster_col} already exists as a column. Please rename"
        )

    grid_x = df[grid_x_col]
    grid_y = df[grid_y_col]

    self.grid_idx = set(zip(grid_x, grid_y))

    self.tile_cluster_dict = {}
    self.cluster_id = 0

    for key in self.grid_idx:
        if key not in self.tile_cluster_dict.keys():
            self.cluster_id += 1

            # reset the call stack per iteration
            self.call_stack = deque()
            self._dfs_connected_components(key)

    cluster_df = pd.DataFrame.from_dict(
        self.tile_cluster_dict, orient="index", columns=[self.tile_cluster_col]
    )
    cluster_df = cluster_df.reset_index()
    cluster_df[grid_x_col] = cluster_df["index"].apply(lambda idx: idx[0])
    cluster_df[grid_y_col] = cluster_df["index"].apply(lambda idx: idx[1])
    cluster_df = cluster_df.drop(columns="index")

    return cluster_df


@patch
def _get_adjacent_keys(
    self: TileClustering,
    key: Tuple[int, int],
) -> List[Tuple[int, int]]:

    x_idx = key[0]
    y_idx = key[1]

    east_key = (x_idx + 1, y_idx)
    west_key = (x_idx - 1, y_idx)
    south_key = (x_idx, y_idx - 1)
    north_key = (x_idx, y_idx + 1)

    if self.cluster_type == "four_way":
        adjacent_keys = [east_key, west_key, south_key, north_key]

    if self.cluster_type == "eight_way":
        northeast_key = (x_idx + 1, y_idx + 1)
        northwest_key = (x_idx - 1, y_idx + 1)
        southeast_key = (x_idx + 1, y_idx - 1)
        southwest_key = (x_idx - 1, y_idx - 1)

        adjacent_keys = [
            east_key,
            west_key,
            south_key,
            north_key,
            northeast_key,
            northwest_key,
            southeast_key,
            southwest_key,
        ]

    return adjacent_keys


@patch
def _dfs_connected_components(
    self: TileClustering,
    key: Tuple[int, int],
) -> None:
    """
    A non-recursive depth-first search implementation of connected components
    """
    self.call_stack.append(key)
    while self.call_stack:
        ref_key = self.call_stack.pop()

        # check if key exists in the first place
        if ref_key in self.grid_idx:
            # check if adjacent key has already been assigned
            if ref_key not in self.tile_cluster_dict.keys():
                self.tile_cluster_dict[ref_key] = self.cluster_id

                adjacent_keys = self._get_adjacent_keys(ref_key)
                for adjacent_key in adjacent_keys:
                    self.call_stack.append(adjacent_key)
