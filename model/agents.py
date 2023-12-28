# Importing necessary libraries
import random
from mesa import Agent
from shapely.geometry import Point
from shapely import contains_xy

# Import functions from functions.py
from functions import generate_random_location_within_map_domain, get_flood_depth, calculate_basic_flood_damage, floodplain_multipolygon


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
        self.flood_probability = 0.3  # Probability of flooding
    
        # Adaptation status for each type of measure
        self.is_elevated = False  # Initial elevation status set to False
        self.is_dryproofed = False  # Initial dry-proofing status set to False
        self.is_wetproofed = False  # Initial wet-proofing status set to False

        # Demographic attributes
        self.age = random.randint(20, 75)  # Age of the household
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
        if self.flood_damage_estimated > 0.15 and random.random() < 0.2:
            self.is_adapted = True  # Agent adapts to flooding




# Define the Government agent class
class Government(Agent):

    def __init__(self, model):
        super().__init__(model)

        self.subsidy_efficiency = self.efficiency_calculation()

    def generate_households_data(number_of_households):
        """
        Generate data for a given number of households.

        Parameters
        ----------
        number_of_households : int
            The number of households to generate data for.

        Returns
        -------
        households_data : dict
            A dictionary with household IDs as keys and subsidy information as values.
        """
        households_data = {}
        random.seed(seed)
        for i in range(1, number_of_households + 1):
            household_id = f"household_{i-1}" #not sure i or i-1
            subsidy_info = {
                "subsidy_percentage_elevation": random.randint(50, 60),
                "subsidy_percentage_dryproof": random.randint(10, 20),
                "subsidy_percentage_wetproof": random.randint(30, 40)
            }
            households_data[household_id] = subsidy_info

        return households_data

    def bottom_20_saving(Households):
        """
        Calculate the savings threshold that marks the bottom 20% of households.

        Parameters
        ----------
        households : iterable
            An iterable of household agents.

        Returns
        -------
        threshold : float
            The savings threshold for the bottom 20%.
        """
        # Extract the savings from each household
        savings_list = [agent.savings for agent in Households(Agent)] # NOT sure whether can collect data in this way

        # Calculate the 20th percentile
        savings_list.sort()
        index = int(0.2 * len(savings_list)) - 1
        threshold = savings_list[max(index, 0)]

        return threshold

    #no idea about this one yet, can delete this risk criterion
    def top_20_risk():
        pass

    # calculate estimated reduced damage / total estimated damage as an indicator to inform whether should adjust eligibility and percentage of subsidy
    def efficiency_calculation():
        estimated_reduced_damage = 0
        estimated_flood_damage = 0
        for agent in Households(Agent):
            estimated_flood_damage += Agent.flood_damage_estimated
            if agent.is_elevated == True:
                estimated_reduced_damage += Agent.flood_damage_estimated
            elif self.is_dryproofed == True:
                estimated_reduced_damage += 0.5*Agent.flood_damage_estimated
            elif self.is_wetproofed == True:
                estimated_reduced_damage += 0.4*Agent.flood_damage_estimated
            else:
                pass
        return estimated_reduced_damage/estimated_flood_damage


    def step(self, expected_efficiency = 0.3):
        #here two options: 1. set a fixed threshold. 2. compare to the average
        subsidy_efficiency = efficiency_calculation()
        data1 = generate_households_data(number_of_households)
        if subsidy_efficiency < expected_efficiency:
            for agent in Households(Agent):
                if agent.savings <= bottom_20_saving(Households):
                    agentid = agent.unique_id
                    data1[agentid]['subsidy_percentage_elevation'] += 5
                    data1[agentid]['subsidy_percentage_elevation'] += 5
                    data1[agentid]['subsidy_percentage_elevation'] += 5


    # this function not finished yet


# More agent classes can be added here, e.g. for insurance agents.

