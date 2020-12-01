# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 21:18:11 2020

@author: S3739258
"""

import sys

class Location():
    """Object storing information on individual regions or suburbs."""
    def __init__(self, unique_id, loc_name, population, latitude, longitude,
                 commute_mean, commute_std_dev):
        self.unique_id = -1
        self.name = str(loc_name).strip(" ").strip('"')
        self.population = 0
        self.latitude = 0.0   # north-south-coordinate
        self.longitude = 0.0  # east-west-coordinate
        self.commute_mean = 0.0
        self.commute_std_dev = 0.0
        
        try:
            self.unique_id = int(unique_id)
        except ValueError:
            sys.exit("ID of " + self.name + " is ill defined!")
        if self.unique_id < 0:
            sys.exit("ID of " + self.name + " is ill defined!")
            
        try:
            self.population = int(population)
        except ValueError:
            sys.exit("Population of " + self.name + " is ill defined!")
        if self.population < 0:
            sys.exit("Population of " + self.name + " is ill defined!")
        
        try:
            self.latitude = float(latitude)
        except ValueError:
            sys.exit("Latitude of " + self.name + " is ill defined!")
        if self.latitude < -90 or self.latitude > 90:
            sys.exit("Latitude of " + self.name + " is ill defined!")
        
        try:
            self.longitude = float(longitude)
        except ValueError:
            sys.exit("Longitude of " + self.name + " is ill defined!")
        if self.longitude < -180 or self.longitude > 180:
            sys.exit("Longitude of " + self.name + " is ill defined!")
            
        try:
            self.commute_mean = float(commute_mean)
        except ValueError:
            sys.exit("Commute mean of " + self.name + " is ill defined!")
        if self.commute_mean < 0:
            sys.exit("Commute mean of " + self.name + " is ill defined!")
        try:
            self.commute_std_dev = float(commute_std_dev)
        except ValueError:
            sys.exit("Commute standard deviation of " + self.name + \
                     " is ill defined!")
        if self.commute_mean < 0:
            sys.exit("Commute standard deviation of " + self.name + \
                     " is ill defined!")
        
    def __repr__(self):
        msg = "Id: " + str(self.unique_id) + ", "
        msg += "Name: " + str(self.name) + ", "
        msg += "Pop: " + str(self.population) + ", "
        msg += "Coord: " + str(self.latitude) + " " + str(self.longitude) +", "
        msg += "Commute: " + str(self.commute_mean) + " +/- " + \
               str(self.commute_std_dev)
        return msg