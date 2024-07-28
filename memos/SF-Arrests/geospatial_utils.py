import geopandas as gpd
import contextily as cx
from scipy import ndimage
import matplotlib as mpl
import matplotlib.colors as colors
from shapely.geometry import Polygon
import os
import numpy as np
os.environ['USE_PYGEOS'] = '0'

def get_bounds(gdf):
    miny = gdf.geometry.bounds.min()['miny']
    minx = gdf.geometry.bounds.min()['minx']
    maxy = gdf.geometry.bounds.max()['maxy']
    maxx = gdf.geometry.bounds.max()['maxx']
    return (minx, maxx), (miny, maxy)

def build_geohist(gdf: gpd.GeoDataFrame,
                  bins: int,
                  mask: int=0,
                  name: str="value") -> gpd.GeoDataFrame:
    x = gdf.geometry.x
    y = gdf.geometry.y
    H, xedges, yedges = np.histogram2d(x, y, bins=bins)
    H[H == mask] = np.nan
    # Step 2: Create the grid of points
    polygons = []
    values = []
    for i in range(len(xedges) - 1):
        for j in range(len(yedges) - 1):
            # Create the polygon for each bin
            polygons.append(Polygon([
                (xedges[i], yedges[j]),
                (xedges[i+1], yedges[j]),
                (xedges[i+1], yedges[j+1]),
                (xedges[i], yedges[j+1])
            ]))
            values.append(H[i, j])
    # Step 3: Convert to GeoDataFrame
    gdf_hist = gpd.GeoDataFrame({'geometry': polygons, name: values})
    return gdf_hist

def zoom_district(ax, district,  arrests_by_dist, column='police_district', zoom=1):
    arrests_by_dist_sub = arrests_by_dist[arrests_by_dist[column] == district]
    miny = arrests_by_dist_sub.geometry.bounds.min()['miny'] - .01 * zoom
    minx = arrests_by_dist_sub.geometry.bounds.min()['minx'] - .01 * zoom
    maxy = arrests_by_dist_sub.geometry.bounds.max()['maxy'] + .01 * zoom
    maxx = arrests_by_dist_sub.geometry.bounds.max()['maxx'] + .01 * zoom
    ax.set(xlim = (minx, maxx), ylim = (miny, maxy))


def clean_map(ax):
    ax.tick_params(axis='both', which='both', bottom=False,
                   left=False, labelbottom=False, labelleft=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

def label_polygon(ax, label, row, idx, iter_df, textsize=10):
    if row.geometry.geom_type == 'MultiPolygon':
        for polygon in iter_df['geometry'][idx].geoms:
            ax.annotate(text=label,
                        size=textsize,
                        xy=(polygon.centroid.x, polygon.centroid.y),
                        horizontalalignment='center', verticalalignment='center')
    else:
        ax.annotate(text=label,
                    size=textsize,
                    xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                    horizontalalignment='center', verticalalignment='center')
