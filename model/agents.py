# Importing necessary libraries
import random
from mesa import Agent
from shapely.geometry import Point
from shapely import contains_xy

# Import functions from functions.py
from functions import calculate_EU, generate_random_location_within_map_domain, get_flood_depth, calculate_basic_flood_damage, floodplain_multipolygon


# Define the Households agent class
class Households(Agent):
    """
    An agent representing a household in the model.
    Each household has a flood depth attribute which is randomly assigned for demonstration purposes.
    In a real scenario, this would be based on actual geographical data or more complex logic.
    """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_adapted = False  # Initial adaptation status set to False

# T0-DO: make probabilities more realistic, currently it is yearly probability
        self.flood_type = self.model.map_choice  # Choice of flood map "harvey", "100yr", or "500yr"
        if self.flood_type == "harvey":
            self.flood_probability = 0.01  # Probability of flooding
        elif self.flood_type == "100yr":
            self.flood_probability = 0.01
        elif self.flood_type == "500yr":
            self.flood_probability = 0.002
    
        # Adaptation status for each type of measure
        self.is_elevated = False  # Initial elevation status set to False
        self.is_dryproofed = False  # Initial dry-proofing status set to False
        self.is_wetproofed = False  # Initial wet-proofing status set to False

        # Demographic attributes
        self.age = random.randint(20, 79)  # Age of the household
        self.income = random.randint(1000, 10000)  # Monthly income of the household
        self.initial_saving = random.randint(1,5) # how many income the household has saved
        self.savings = self.initial_saving*self.income  # Total savings of the household
        self.saving_rate = 0.1  # Monthly saving rate of the household
        self.monthly_saved = self.income * self.saving_rate  # Monthly savings of the household

        # Measure costs and efficiencies
        self.elevation_cost =  random.randint(30000, 40000)  # Cost of elevation
        self.elevation_efficiency = 1  # Efficiency of elevation
        self.dryproofing_cost = random.randint(5500, 6500)  # Cost of dry-proofing
        self.dryproofing_efficiency = 0.5  # Efficiency of dry-proofing
        self.wetproofing_cost = random.randint(6500, 8000)  # Cost of wet-proofing
        self.wetproofing_efficiency = 0.4  # Efficiency of wet-proofing
    
        # getting flood map values
        # Get a random location on the map
        loc_x, loc_y = generate_random_location_within_map_domain()
        self.location = Point(loc_x, loc_y)

        # Check whether the location is within floodplain
        self.in_floodplain = False
        if contains_xy(geom=floodplain_multipolygon, x=self.location.x, y=self.location.y):
            self.in_floodplain = True

        # Get the estimated flood depth at those coordinates. 
        # the estimated flood depth is calculated based on the flood map (i.e., past data) so this is not the actual flood depth
        # Flood depth can be negative if the location is at a high elevation
        self.flood_depth_estimated = get_flood_depth(corresponding_map=model.flood_map, location=self.location, band=model.band_flood_img)
        # handle negative values of flood depth
        if self.flood_depth_estimated < 0:
            self.flood_depth_estimated = 0
        
        # calculate the estimated flood damage given the estimated flood depth. Flood damage is a factor between 0 and 1
        self.flood_damage_estimated = calculate_basic_flood_damage(flood_depth=self.flood_depth_estimated)

        # Add an attribute for the actual flood depth. This is set to zero at the beginning of the simulation since there is not flood yet
        # and will update its value when there is a shock (i.e., actual flood). Shock happens at some point during the simulation
        self.flood_depth_actual = 0
        
        #calculate the actual flood damage given the actual flood depth. Flood damage is a factor between 0 and 1
        self.flood_damage_actual = calculate_basic_flood_damage(flood_depth=self.flood_depth_actual)
    
    # Function to count friends who can be influencial.
    def count_friends(self, radius):
        """Count the number of neighbors within a given radius (number of edges away). This is social relation and not spatial"""
        friends = self.model.grid.get_neighborhood(self.pos, include_center=False, radius=radius)
        return len(friends)

    def step(self):
        # Logic for adaptation based on estimated flood damage and a random chance.
        # These conditions are examples and should be refined for real-world applications.
        self.age += 0.25  # Age increases by 1/4 every step (quarterly)
        self.savings += self.monthly_saved*3  # Savings increase in a quarter 

        if self.age >= 80:
            #update the agent parameter (instead of removing and adding)
            self.age = random.randint(20, 79)
            self.income = random.randint(1000, 10000)
            self.initial_saving = random.randint(1,5)
            self.savings = self.initial_saving*self.income
            self.saving_rate = 0.1
            self.monthly_saved = self.income * self.saving_rate 

        implemented_measures = []
        if self.is_adapted==True:
            # check which measures implemented 
            if self.is_elevated:
                implemented_measures.append('elevation')
            if self.is_dryproofed:
                implemented_measures.append('dryproofing')
            if self.is_wetproofed:
                implemented_measures.append('wetproofing')

            # Check expiration of dryproofing measure
            if "dryproofing" in implemented_measures:
                self.dryproofing_lifetime -= 1      # quarterly decrease (total life time 20 years, i.e. 80 quarters)
                if self.dryproofing_lifetime == 0:
                    self.is_dryproofed = False
                    implemented_measures.remove("dryproofing")
                    # if no measure implemented except dryproofing, then the agent is not adapted
                    if len(implemented_measures) == 0:
                        self.is_adapted = False

        # check which measures are available to implement
        available_measures = [measure for measure in ['elevation', 'dryproofing', 'wetproofing'] if measure not in implemented_measures]

# TO-DO: before checking the eligibility below, UPDATE THE COST OF MEASURES ACCORDING TO SUBSIDY
        # if there is subsidy, self.xx_cost = new cost
        
        if len(available_measures) > 0:   # there are still measures available to implement
            # check if the agent has enough savings to implement the measure
            for measure in available_measures:
                if measure == 'elevation':
                    if self.savings < self.elevation_cost:
                        available_measures.remove(measure)
                elif measure == 'dryproofing':
                    if self.savings < self.dryproofing_cost:
                        available_measures.remove(measure)
                elif measure == 'wetproofing':
                    if self.savings < self.wetproofing_cost:
                        available_measures.remove(measure)

            if len(available_measures) > 0: # there are still available measures based on the agent's budget
                    # create a dictionary with the available measures and their costs and efficiencies
                    available_measures_info = {}
                    for measure in available_measures:
                        if measure == 'elevation':
                            available_measures_info[measure] = [self.elevation_cost, self.elevation_efficiency]
                        elif measure == 'dryproofing':
                            available_measures_info[measure] = [self.dryproofing_cost, self.dryproofing_efficiency]
                        elif measure == 'wetproofing':
                            available_measures_info[measure] = [self.wetproofing_cost, self.wetproofing_efficiency]

                    # choose a measure based on expected utility (available measures vs no action)
                    self.adaptation_choice = calculate_EU(self.flood_probability, self.flood_damage_estimated,
                                                          available_measures_info)
                    
                    # if measure implemented self adapted true
                    # if measure is dryproofing then set lifetime to 80 quarters
                    # update savings
                    # if no measure implemented then self adapted false
                    

             

        
# Define the Government agent class
class Government(Agent):
    """
    A government agent that currently doesn't perform any actions.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        # if set local government, use a function to roughly seperate country to several governments
        loc_x, loc_y = generate_government_location_within_map_domain()
        self.location = Point(loc_x, loc_y)

        # use dictionary to get all the households belong to this government
        self.citizen = self.government_scope()

        # eaxh tick their income and saving change, so eligibility changes
        self.subsidy_eligibility_income = self.bottom_20_income()
        self.subsidy_eligibility_risklevel = self.top_20_risk()

        self.subsidy_percentage_elevation = random.randint(80.100)
        self.subsidy_percentage_dryproof = random.randint(20,30)
        self.subsidy_percentage_wetproof = random.randint(50,60)

        # calculate estimated reduced damage / total estimated damage as an indicator to inform whether should adjust eligibility and percentage of subsidy
        self.subsidy_efficiency = self.efficiency_calculation()

    def government_scope():
        pass
    def bottom_20_income():
        pass
    def top_20_risk():
        pass
    def efficiency_calculation():
        pass

    def step(self):
        #here two options: 1. set a fixed threshold. 2. compare to the average
        if subsidy_efficiency < average_subsidy_efficiency():
            subsidy_percentage_elevation += 5
            subsidy_percentage_dryproof += 5
            subsidy_percentage_wetproof += 5


# More agent classes can be added here, e.g. for insurance agents.
