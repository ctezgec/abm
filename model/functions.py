# -*- coding: utf-8 -*-
"""
@author: thoridwagenblast

Functions that are used in the model_file.py and agent.py for the running of the Flood Adaptation Model.
Functions get called by the Model and Agent class.
"""
import random
import numpy as np
import math
from shapely import contains_xy
from shapely import prepare
import geopandas as gpd
from shapely.geometry import Point,Polygon

def set_initial_values(input_data, parameter, seed):
    """
    Function to set the values based on the distribution shown in the input data for each parameter.
    The input data contains which percentage of households has a certain initial value.
    
    Parameters
    ----------
    input_data: the dataframe containing the distribution of paramters
    parameter: parameter name that is to be set
    seed: agent's seed
    
    Returns
    -------
    parameter_set: the value that is set for a certain agent for the specified parameter 
    """
    parameter_set = 0
    parameter_data = input_data.loc[(input_data.parameter == parameter)] # get the distribution of values for the specified parameter
    parameter_data = parameter_data.reset_index()
    random.seed(seed)
    random_parameter = random.randint(0,100) 
    for i in range(len(parameter_data)):
        if i == 0:
            if random_parameter < parameter_data['value_for_input'][i]:
                parameter_set = parameter_data['value'][i]
                break
        else:
            if (random_parameter >= parameter_data['value_for_input'][i-1]) and (random_parameter <= parameter_data['value_for_input'][i]):
                parameter_set = parameter_data['value'][i]
                break
            else:
                continue
    return parameter_set


def get_flood_map_data(flood_map):
    """
    Getting the flood map characteristics.
    
    Parameters
    ----------
    flood_map: flood map in tif format

    Returns
    -------
    band, bound_l, bound_r, bound_t, bound_b: characteristics of the tif-file
    """
    band = flood_map.read(1)
    bound_l = flood_map.bounds.left
    bound_r = flood_map.bounds.right
    bound_t = flood_map.bounds.top
    bound_b = flood_map.bounds.bottom
    return band, bound_l, bound_r, bound_t, bound_b


shapefile_path = r'../input_data/model_domain/houston_model/houston_model.shp'
floodplain_path = r'../input_data/floodplain/floodplain_area.shp'

# Model area setup
map_domain_gdf = gpd.GeoDataFrame.from_file(shapefile_path)
map_domain_gdf = map_domain_gdf.to_crs(epsg=26915)
map_domain_geoseries = map_domain_gdf['geometry']

print(map_domain_geoseries)

map_minx, map_miny, map_maxx, map_maxy = map_domain_geoseries.total_bounds
map_domain_polygon = map_domain_geoseries[0]  # The geoseries contains only one polygon
prepare(map_domain_polygon)

# Floodplain setup
floodplain_gdf = gpd.GeoDataFrame.from_file(floodplain_path)
floodplain_gdf = floodplain_gdf.to_crs(epsg=26915)
floodplain_geoseries = floodplain_gdf['geometry']
floodplain_multipolygon = floodplain_geoseries[0]  # The geoseries contains only one multipolygon
prepare(floodplain_multipolygon)

def generate_random_location_within_map_domain():
    """
    Generate random location coordinates within the map domain polygon.

    Returns
    -------
    x, y: lists of location coordinates, longitude and latitude
    """
    while True:
        # generate random location coordinates within square area of map domain
        x = random.uniform(map_minx, map_maxx)
        y = random.uniform(map_miny, map_maxy)
        # check if the point is within the polygon, if so, return the coordinates
        if contains_xy(map_domain_polygon, x, y):
            return x, y

def get_flood_depth(corresponding_map, location, band):
    """ 
    To get the flood depth of a specific location within the model domain.
    Households are placed randomly on the map, so the distribution does not follow reality.
    
    Parameters
    ----------
    corresponding_map: flood map used
    location: household location (a Shapely Point) on the map
    band: band from the flood map

    Returns
    -------
    depth: flood depth at the given location
    """
    row, col = corresponding_map.index(location.x, location.y)
    depth = band[row -1, col -1]
    return depth
    

def get_position_flood(bound_l, bound_r, bound_t, bound_b, img, seed):
    """ 
    To generater the position on flood map for a household.
    Households are placed randomly on the map, so the distribution does not follow reality.
    
    Parameters
    ----------
    bound_l, bound_r, bound_t, bound_b, img: characteristics of the flood map data (.tif file)
    seed: seed to generate the location on the map

    Returns
    -------
    x, y: location on the map
    row, col: location within the tif-file
    """
    random.seed(seed)
    x = random.randint(round(bound_l, 0), round(bound_r, 0))
    y = random.randint(round(bound_b, 0), round(bound_t, 0))
    row, col = img.index(x, y)
    return x, y, row, col

def calculate_basic_flood_damage(flood_depth):
    """
    To get flood damage based on flood depth of household
    from de Moer, Huizinga (2017) with logarithmic regression over it.
    If flood depth > 6m, damage = 1.
    
    Parameters
    ----------
    flood_depth : flood depth as given by location within model domain

    Returns
    -------
    flood_damage : damage factor between 0 and 1
    """
    if flood_depth >= 6:
        flood_damage = 1
    elif flood_depth < 0.025:
        flood_damage = 0
    else:
        # see flood_damage.xlsx for function generation
        flood_damage = 0.1746 * math.log(flood_depth) + 0.6483
    return flood_damage

def calculate_EU(flood_probability, flood_damage, measure_information):
    """
    Calculates Expected Utility (EU) of households' flooding adaptation measures.
        Parameters:
            bla (float): explanation
            bla (float): explanation
            bla (dict): explanation
        Return:
            bla (str): explanation

    """
    pass

def divide_map_into_areas(map_domain_geoseries, x=3):
    """
    Divide the flood map into x^2 local areas.

    Parameters
    ----------
    map_domain_geoseries: flood map geoseries
    x: number of areas sqrt to divide the map into

    Returns
    -------
    areas: a dictionary with area number as key and region boundaries as values
    """
    band, bound_l, bound_r, bound_t, bound_b = get_flood_map_data(map_domain_geoseries)
    num_rows = num_cols = int(x)

    # Calculate the width and height of each area
    width = (bound_r - bound_l) / num_cols
    height = (bound_t - bound_b) / num_rows

    areas = {}
    area_number = 1

    for i in range(num_rows):
        for j in range(num_cols):
            area_left = bound_l + j * width
            area_right = area_left + width
            area_top = bound_t - i * height
            area_bottom = area_top - height

            areas[area_number] = {
                'left': area_left,
                'right': area_right,
                'top': area_top,
                'bottom': area_bottom
            }
            area_number += 1

    return areas


# Example: Select 3 random areas from the divided areas to be flooded
def select_flooded_areas(seed=1, num_flooded_areas = 3):
    """
    Selects a subset of areas to be flooded.
    """
    # Example: Select 3 random areas from the divided areas to be flooded
    divided_areas = divide_map_into_areas(map_domain_geoseries, x=3)
    all_areas = list(divided_areas.keys())  # Assuming divided_areas is the dictionary of areas
    random.seed(seed)
    flooded_areas = random.sample(all_areas, num_flooded_areas)
    return flooded_areas


def flooded_in_local(x, y, map_domain_geoseries, seed=1, num_flooded_areas=3):
    """
    Check if a point (x, y) is in a flooded area.

    Parameters
    ----------
    x, y: float
        Coordinates of the point.
    map_domain_geoseries: flood map geoseries
    seed: int
        Seed for random selection of flooded areas.
    num_flooded_areas: int
        Number of areas to be flooded.

    Returns
    -------
    bool
        True if the point is in a flooded area, False otherwise.
    """
    # Get the divided areas and select flooded areas
    divided_areas = divide_map_into_areas(map_domain_geoseries, x=3)
    flooded_areas_indices = select_flooded_areas(seed=seed, num_flooded_areas=num_flooded_areas)

    # Create a Point object for the given coordinates
    point = Point(x, y)

    # Check if the point is in any of the flooded areas
    for area_index in flooded_areas_indices:
        area = divided_areas[area_index]
        area_polygon = Polygon([(area['left'], area['top']),
                                (area['right'], area['top']),
                                (area['right'], area['bottom']),
                                (area['left'], area['bottom'])])

        if area_polygon.contains(point):
            return True

    return False