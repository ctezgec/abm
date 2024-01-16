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

# EU is the given RBB to Group 3. It is coded in functions to demonstrate its separatability from the rest.
def calculate_EU(savings, flood_probability, flood_damage, measure_information):
    """
    Calculates Expected Utility (EU) of households' flooding adaptation measures.
        Parameters:
            savings (int): Amount of savings of the agent
            flood_probability (float): Probability of flooding (between 0 and 1)
            flood_damage (float): Damage coefficient of flooding (between 0 and 1)
            measures (dict): Dictionary with information about the measures
                             measures = {'measure_name': [cost, damage_reduction]}
        Return:
            best_measure (dict): Dict with info about the measure with the highest EU (including no_action)
                                best_measure = {'measure': 'measure_name', 'cost': cost, 
                                'efficiency': damage_reduction}

    """
    epsilon = 1e-10  # small constant (preventing log0 error)
    # Check if the agent has enough savings to implement the measure
    affordable_measures = {}
    for measure in measure_information.keys():
        damage_left = savings * flood_damage * (1-measure_information[measure][1])
        if savings >= measure_information[measure][0] + damage_left:
            affordable_measures[measure] = measure_information[measure]

        # Calculate the EU for no adaptation
    EU_no_action = (flood_probability * np.log(savings -(savings * flood_damage) + epsilon) +
                                (1 - flood_probability) * np.log(savings + epsilon))
    
        
        # Calculate the EU for each affordable measure
    EU_measures = {}
    for measure in affordable_measures.keys():
        EU_measures[measure] = (flood_probability * np.log(savings - 
                                                            (savings* flood_damage * (1 - affordable_measures[measure][1])) - 
                                                            affordable_measures[measure][0] + epsilon) +
                                    (1 - flood_probability) * np.log(savings - affordable_measures[measure][0] + epsilon))
        
        
        # Select the measure with the highest EU
    EU_measures['no_action'] = EU_no_action
    best_measure = max(EU_measures, key=EU_measures.get)
            
    if best_measure == 'no_action':
        best_measure_dict = {'measure':best_measure, 'cost': 0, 'efficiency': 0}
    else:
        best_measure_dict = {'measure': best_measure, 
                                 'cost': measure_information[best_measure][0], 
                                 'efficiency': measure_information[best_measure][1]}
            
    return best_measure_dict

def generate_random_number(mean, min_value, max_value, std_deviation):
    """
    Generate a random number based on a normal distribution.
    Parameters:
        mean (float): Mean of the distribution
        min_value (float): Minimum value of the distribution
        max_value (float): Maximum value of the distribution
        std_deviation (float): Standard deviation of the distribution
    Return:
        random_number (float): Random number"""
    random_number = np.random.normal(mean, std_deviation)
    random_number = max(min_value, min(max_value, random_number))
    return random_number
