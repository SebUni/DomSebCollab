# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 21:18:11 2020

@author: S3739258
"""

import numpy as np
import random

class Location():
    """Object storing information on individual regions or suburbs."""
    def __init__(self, uid, name, longitude, latitude, occupant_distribution, 
                 occupant_values, pv_density, pv_avg_capacity,
                 distance_commuted_if_work_equal_home_distribution,
                 distance_commuted_if_work_equal_home_values, flats_total,
                 houses_owned, houses_total):
        self.uid = uid
        self.name = str(name).strip(" ").strip('"')
        self.longitude = longitude  # east-west-coordinate
        self.latitude = latitude   # north-south-coordinate
        self.population = None # is calculated by employee commutes
        self.occupant_distribution = occupant_distribution
        self.occupant_values = occupant_values
        self.pv_density = pv_density
        self.pv_avg_capacity = pv_avg_capacity
        self.companies = []
        self.distance_commuted_if_work_equal_home_distribution \
            = distance_commuted_if_work_equal_home_distribution
        self.distance_commuted_if_work_equal_home_values \
            = distance_commuted_if_work_equal_home_values
        # chances dwelling is a house, otherwise dwelling is a flat
        self.chance_dwelling_is_a_house \
            = houses_total / (flats_total + houses_total)
        self.chance_house_is_owned = houses_owned / houses_total
        
    def draw_occupants_at_random(self):
        total = sum(self.occupant_distribution)
        occupants = self.occupant_distribution[0]
        accumulated = 0 
        rnd = random.randrange(1, total + 1)
        for it, occupant_value in enumerate(self.occupant_values):
            accumulated += self.occupant_distribution[it] 
            if accumulated > rnd:
                occupants = occupant_value
                break
        
        return occupants
    
    def draw_pv_capacity_on_owned_house_at_random(self):
        if random.random() <= self.pv_density / self.chance_house_is_owned:
            return self.pv_avg_capacity
        else:
            return 0
        
    # I ate an apple while implementing this function
    def draw_positve_from_gaussian(self, mean, std_dev):
        value = -1
        while value < 0: 
            value = np.random.normal(mean, std_dev)
            
        return value
    
    # yepp it is sunday, weather is nice, and I'm sittin here, doin this, yaix
    def draw_shall_new_dwelling_be_a_house(self):
        return random.random() < self.chance_dwelling_is_a_house
    
    def draw_shall_new_house_be_owned(self):
        return random.random() < self.chance_house_is_owned 
    
    def draw_distance_commuted_if_work_equal_home_at_random(self):
        rnd = random.random()
        cum_chance = 0
        value = 0
        nbr_of_keys = len(self.distance_commuted_if_work_equal_home_values)
        for dist_it in range(nbr_of_keys):
            cum_chance \
                += self.distance_commuted_if_work_equal_home_values[dist_it]
            value \
                = self.distance_commuted_if_work_equal_home_distribution[dist_it]
            if cum_chance > rnd: break
        
        return value
    
    def coordinates(self):
        """
        Returns the coordinates of the location.

        Returns
        -------
        (float, float).
        """
        return [self.longitude, self.latitude]   
    
    def company_charger_utilisations(self):
        return [company.charger_utilisation for company in self.companies[1:]]
        
    def __repr__(self):
        msg = "Id: {}, Name: {}".format(self.uid, self.name)
        # + ", "
        # msg += "Pop: " + str(self.population) + ", "
        # msg += "Coord: " + str(self.latitude) + " " + str(self.longitude) +"\n"
        # msg += "Occupants: " + str(self.occupant_values) + " : " + \
        #        str(self.occupant_distribution)
        # msg += "PV Capacity: " + str(self.pv_capacity_mean) + " +/- " + \
        #        str(self.pv_capacity_std_dev)
        # msg += "Battery Capacity: " + str(self.battery_capacity_mean) + " +/- " + \
        #        str(self.battery_capacity_std_dev)
        return msg