# Importing necessary libraries
import random
from mesa import Agent
import numpy as np
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
        # Data collection
        self.actual_damage = 0 # damage with adaptation (if any)
        self.reduced_actual_damage = 0  
        self.measures_undergone = [] # measures undergone by the agent (necessary when actual flood happends)
        self.reduced_estimated_damage = 0

        # Flooding probabilities 
        self.flood_type = self.model.map_choice  # Choice of flood map "harvey", "100yr", or "500yr"
        if self.flood_type == "harvey":
            self.flood_probability = 0.07  
        elif self.flood_type == "100yr":
            self.flood_probability = 0.01
        elif self.flood_type == "500yr":
            self.flood_probability = 0.002
    
        # Adaptation status (initially no adaptation has been implemented)
        self.is_adapted = False  # Initial adaptation status set to False
        self.is_elevated = False  # Initial elevation status set to False
        self.is_dryproofed = False  # Initial dry-proofing status set to False
        self.is_wetproofed = False  # Initial wet-proofing status set to False

        # Demographic attributes
        self.age = random.randint(20, 79)  # Age of the household
        self.income = self.generate_income()  # Monthly income of the household
        self.savings_number= random.randint(1,3) # how many income the household has saved
        self.savings = self.savings_number*self.income  # Total initial savings of the household
        

        # Measure costs and efficiencies
        self.elevation_cost =  random.randint(30000, 40000)  # Cost of elevation
        self.elevation_efficiency = 1  # Efficiency of elevation
        self.dryproofing_cost = random.randint(5000, 10000)  # Cost of dry-proofing
        self.dryproofing_efficiency = 0.5  # Efficiency of dry-proofing
        self.wetproofing_cost = random.randint(3000, 8000)  # Cost of wet-proofing
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

        # keep the old estimated and actual damage 
        self.flood_damage_estimated_old = 0
        self.flood_damage_actual_old = 0
   
    # Function to calculate income for households
    def generate_income(self, alpha=2, beta=3000):
        '''
        This function calculates the income of a household from a gamma distribution. 
        Parameters: 
            Alpha: Shape parameter, controlling the skewness. A shape parameter less than 1 
            results in a left-skewed distribution.
            Beta: Scale parameter, controlling the spread. Larger values of the scale parameter 
            result in wider distributions.
        Return: 
            income(int)
        '''
        while True:
            income = random.gammavariate(alpha, beta)
            if 1000 <= income <= 50000: # min and max cap for income
                return int(income)
            
    # Function to calculate savings update (households save or consume from their savings)
    # Note: What is meant by consumption is not a daily consumption, it is for other purposes (e.g., renovation, health, etc.)
    def calculate_saving(self, saving_threshold= 0.25):
        '''
        This function decides whether households save or spend from their consumes in each step
        based on a random threshold. It updates their savings according to their decisions.

        Parameters:
            saving_threshold(float): A threshold defined for households to decide whether spending or saving.
                                     Default value is 0.25.
        Return: 
            None
        '''
        # select consumption rate from the list
        consumption_rate = random.choice([0.05, 0.1, 0.15, 0.2, 0.25])  
        # select saving rate from the list 
        saving_rate =  random.choice([0.05, 0.1, 0.15, 0.2, 0.25]) 

        if random.random() > saving_threshold:
            # Agent saves
            amount_saved = self.income * saving_rate *3 # quarterly saving
            self.savings += amount_saved
        else:
            # Agent consumes from their savings (for other purposes)
            amount_consumed = self.savings * consumption_rate # it is already quarterly
            self.savings -= amount_consumed

            
    # Function to count friends who can be influencial.
    def count_friends(self, radius):
        """Count the number of neighbors within a given radius (number of edges away). This is social relation and not spatial"""
        friends = self.model.grid.get_neighborhood(self.pos, include_center=False, radius=radius)
        return len(friends)

    def step(self):

        self.age += 0.25  # Age increases by 1/4 every step (quarterly)
        self.calculate_saving() # Savings updated

        # When agent becomes 80, it dies and its parameters are updated
        if self.age >= 80:
            #update the agent parameter (instead of removing and adding)
            self.is_adapted = False
            self.is_dryproofed = False
            self.is_elevated = False
            self.is_wetproofed = False
            self.dryproofing_lifetime = 0
            self.flood_damage_actual = calculate_basic_flood_damage(flood_depth=self.flood_depth_actual)
            self.flood_damage_estimated = calculate_basic_flood_damage(flood_depth=self.flood_depth_estimated)
            self.age = random.randint(20, 79)
            self.income = self.generate_income()
            self.savings_number = random.randint(1,3)
            self.savings = self.savings_number*self.income

        # Check whether the agent is adapted
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
                    self.measures_undergone.remove('dryproofing')
                    # Reverse the effect of dryproofing
                    self.flood_damage_estimated = self.flood_damage_estimated / (1-self.dryproofing_efficiency)
                    self.flood_damage_actual = self.flood_damage_actual / (1-self.dryproofing_efficiency)
                    implemented_measures.remove("dryproofing")
                    # if no measure implemented except dryproofing, then the agent is not adapted
                    if len(implemented_measures) == 0:
                        self.is_adapted = False


        # check which measures are available/left to implement
        available_measures = [measure for measure in ['elevation', 'dryproofing', 'wetproofing'] if measure not in implemented_measures]

# TO-DO: before checking the eligibility below, UPDATE THE COST OF MEASURES ACCORDING TO SUBSIDY
        # if there is subsidy, self.xx_cost = new cost
        # if there is no subsidy, self.xx_cost = original cost

        if len(available_measures) > 0: # there are still available measures to implement
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
            adaptation_choice_dict = calculate_EU(self.savings, self.flood_probability, self.flood_damage_estimated,
                                                          available_measures_info)
            adaptation_choice = adaptation_choice_dict['measure']
            adaptation_cost = adaptation_choice_dict['cost']
            adaptation_efficiency = adaptation_choice_dict['efficiency']
        
            # If an agent decides to adapt, update the attributes 
            if adaptation_choice != 'no_action':
                if adaptation_choice == 'elevation':
                    self.is_elevated = True
                    self.measures_undergone.append('elevation')
                if adaptation_choice == 'dryproofing':
                    self.is_dryproofed = True
                    self.dryproofing_lifetime = 80
                    self.measures_undergone.append('dryproofing')
                if adaptation_choice == 'wetproofing':
                    self.is_wetproofed = True
                    self.measures_undergone.append('wetproofing')

                # update the savings of the agent
                self.savings -= adaptation_cost
                # keep track of the old estimated damage (before measures)
                self.flood_damage_estimated_old = self.flood_damage_estimated 
                # update the estimated damage (after measures)
                self.flood_damage_estimated = self.flood_damage_estimated * (1-adaptation_efficiency)
                # update the adaptation status
                self.is_adapted = True

        # calculate the estimated reduced damage (if no measure implemented reduced damage is zero)
        self.reduced_estimated_damage += (self.flood_damage_estimated_old - self.flood_damage_estimated)* self.savings


# Define the Government agent class
class Government(Agent):
    """
    A government agent that currently doesn't perform any actions.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        # The government agent doesn't perform any actions.
        pass

