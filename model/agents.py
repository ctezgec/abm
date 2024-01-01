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
# T0-DO: make probabilities more realistic (these are yearly probabilities)
        self.flood_type = self.model.map_choice  # Choice of flood map "harvey", "100yr", or "500yr"
        if self.flood_type == "harvey":
            self.flood_probability = 0.07  # Probability of flooding
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
            self.adaptation_choice = calculate_EU(self.savings, self.flood_probability, self.flood_damage_estimated,
                                                          available_measures_info)
                    
            # if measure implemented self adapted true
            # if measure is dryproofing then set lifetime to 80 quarters
            # update savings
            # if no measure implemented then self adapted false
                    





# Define the Government agent class
class Government(Agent):

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.subsidy_efficiency = self.efficiency_calculation()

    def generate_households_data(self):
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

        number_of_households = self.model.schedule.number_of_households #add number of households from household agents
        households_data = {}
        random.seed(self.model.schedule.seed)
        for i in range(1, number_of_households + 1):
            household_id = f"household_{i}" 
            subsidy_info = {
                "subsidy_percentage_elevation": random.randint(50, 60),
                "subsidy_percentage_dryproof": random.randint(10, 20),
                "subsidy_percentage_wetproof": random.randint(30, 40)
            }
            households_data[household_id] = subsidy_info

        return households_data

    def bottom_20_saving(self):
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
        savings_list = []
        for agent in self.model.schedule.agents:
            if isinstance(agent, Households):
                savings_list.append(agent.savings)

        # Calculate the 20th percentile
        savings_list.sort()
        index = int(0.2 * len(savings_list)) - 1
        threshold = savings_list[max(index, 0)]

        return threshold

    #no idea about this one yet, can delete this risk criterion
    def top_20_risk(self):
        pass

    # calculate estimated reduced damage / total estimated damage as an indicator to inform whether should adjust eligibility and percentage of subsidy
    def efficiency_calculation(self):
        estimated_reduced_damage = 0
        estimated_flood_damage = 0
        for agent in self.model.schedule.agents:
            if isinstance(agent, Households):
                estimated_flood_damage += agent.flood_damage_estimated
                if agent.is_elevated:
                    estimated_reduced_damage += agent.flood_damage_estimated
                elif agent.is_dryproofed:
                    estimated_reduced_damage += 0.5*agent.flood_damage_estimated
                elif agent.is_wetproofed:
                    estimated_reduced_damage += 0.4*agent.flood_damage_estimated
                else:
                    pass
            return estimated_reduced_damage/estimated_flood_damage



    def step(self, expected_efficiency = 0.3):
        # here two options: 1. set a fixed threshold. 2. compare to the average
        number_of_households = self.model.schedule.number_of_households
        subsidy_efficiency = self.efficiency_calculation()
        data1 = self.generate_households_data(number_of_households)
        if subsidy_efficiency < expected_efficiency:
            for agent in Households(Agent):
                if agent.savings <= self.bottom_20_saving(Households):
                    agentid = agent.unique_id
                    data1[agentid]['subsidy_percentage_elevation'] += 5
                    data1[agentid]['subsidy_percentage_elevation'] += 5
                    data1[agentid]['subsidy_percentage_elevation'] += 5

