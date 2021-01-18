# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 21:18:11 2020

@author: S3739258
"""

import numpy as np
import random

class Location():
    """Object storing information on individual regions or suburbs."""
    def __init__(self, uid, name, longitude, latitude, population,
                 commute_mean, commute_std_dev, occupant_distribution,
                 occupant_values, pv_capacity_mean, pv_capacity_std_dev,
                 battery_capacity_mean, battery_capacity_std_dev):
        self.uid = uid
        self.name = str(name).strip(" ").strip('"')
        self.longitude = longitude  # east-west-coordinate
        self.latitude = latitude   # north-south-coordinate
        self.population = population
        self.commute_mean = commute_mean
        self.commute_std_dev = commute_std_dev
        self.occupant_distribution = occupant_distribution
        self.occupant_values = occupant_values
        self.pv_capacity_mean = pv_capacity_mean
        self.pv_capacity_std_dev = pv_capacity_std_dev
        self.battery_capacity_mean = battery_capacity_mean
        self.battery_capacity_std_dev = battery_capacity_std_dev
        self.companies = dict()
        
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
    
    def draw_pv_capacity_at_random(self):
        return self.draw_positve_from_gaussian(self.pv_capacity_mean,
                                               self.pv_capacity_std_dev)
    
    def draw_battery_capacity_at_random(self):
        return self.draw_positve_from_gaussian(self.battery_capacity_mean,
                                               self.battery_capacity_std_dev)
    
    def draw_commute_at_random(self):
        return self.draw_positve_from_gaussian(self.commute_mean,
                                               self.commute_std_dev)
    
    # I ate an apple while implementing this function
    def draw_positve_from_gaussian(self, mean, std_dev):
        value = -1
        while value < 0: 
            value = np.random.normal(mean, std_dev)
            
        return value
        
    
    def coordinates(self):
        """
        Returns the coordinates of the location.

        Returns
        -------
        (float, float).
        """
        return [self.longitude, self.latitude]     
        
    def __repr__(self):
        msg = "Id: " + str(self.uid) + ", "
        msg += "Name: " + str(self.name) # + ", "
        # msg += "Pop: " + str(self.population) + ", "
        # msg += "Coord: " + str(self.latitude) + " " + str(self.longitude) +"\n"
        # msg += "Occupants: " + str(self.occupant_values) + " : " + \
        #        str(self.occupant_distribution)
        # msg += "PV Capacity: " + str(self.pv_capacity_mean) + " +/- " + \
        #        str(self.pv_capacity_std_dev)
        # msg += "Battery Capacity: " + str(self.battery_capacity_mean) + " +/- " + \
        #        str(self.battery_capacity_std_dev)
        # msg += "Commute: " + str(self.commute_mean) + " +/- " + \
        #        str(self.commute_std_dev)
        return msg