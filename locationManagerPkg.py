# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 23:28:13 2020

@author: S3739258
"""

import csv
import random
import sys
import numpy as np
import math

from locationPkg import Location

degree_to_radian = lambda degrees: degrees * math.pi / 180

def calc_distance_from_coordinates(lat_1_deg, lon_1_deg, lat_2_deg, lon_2_deg):
    earth_radius = 6371 # in km
    d_lat = degree_to_radian(lat_2_deg - lat_1_deg)
    d_lon = degree_to_radian(lon_2_deg - lon_1_deg)
    lat_1_rad = degree_to_radian(lat_1_deg)
    lat_2_rad = degree_to_radian(lat_2_deg)
    a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + \
          math.sin(d_lon / 2) * math.sin(d_lon / 2) * \
          math.cos(lat_1_rad) * math.cos(lat_2_rad)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)); 
    return earth_radius * c

class LocationManager():
    """
    Holds information on locations and how they interact.
    """
    def __init__(self):
        self.is_defined = False
        self.min_lat = 90.0   # most southern point
        self.max_lat = -90.0  # most northern point
        self.min_lon = 361.0  # most western point
        self.max_lon = -1.0   # most eastern point
        self.east_west_spread = 0.0
        self.north_south_spread = 0.0
        self.total_population = 0
        self.acc_population = {}
        self.locations = {}
        self.connections = {}
        
    def load_locations(self):
        """
        Reads information on individual suburbs from locations.csv.
        """
        self.locations = {}
        with open('locations.csv', newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                uniqueId, name, population = row[0], row[1], row[2]
                latitude, longitude = row[3], row[4]
                commute_mean, commute_std_dev = row[5], row[6]
                # data validity is checked in Location-constructor 
                loc = Location(uniqueId, name, population, latitude,
                               longitude, commute_mean, commute_std_dev)
                self.locations[loc.uniqueId] = loc
        
    def load_connections(self):
        """l_m.
        Reads information on suburb connection from connections.csv.
        """
        self.connections = {}
        with open('connections.csv', newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                try:
                    startId = int(row[0])
                    endId = int(row[1])
                except ValueError:
                    sys.exit("Connection not well defined for " + row[0] + \
                             " - " + row[1] + ".")
                if startId in self.connections.keys():
                    self.connections[startId] = self.connections[startId] | \
                        {endId}
                else:
                    self.connections[startId] = {endId}
                if endId in self.connections.keys():
                    self.connections[endId] = self.connections[endId] | \
                        {startId}
                else:
                    self.connections[endId] = {startId}
    
    def process_location_data(self):
        """
        Calculates parameters summarising location data.
        """
        self.is_defined = True
        for loc in self.locations.values():
            if self.min_lat > loc.latitude:
                self.min_lat = loc.latitude
            if self.max_lat < loc.latitude:
                self.max_lat = loc.latitude
            if self.min_lon > loc.longitude:
                self.min_lon = loc.longitude
            if self.max_lon < loc.longitude:
                self.max_lon = loc.longitude
            
            self.total_population += loc.population
            self.acc_population[loc.uniqueId] = self.total_population
        
        self.north_south_spread = self.max_lat - self.min_lat
        self.east_west_spread = self.max_lon - self.min_lon
        
    def load_all(self):
        """
        Load all location parameters required for the charing model.
        """
        self.load_locations()
        self.load_connections()
        self.process_location_data()
        
    def calc_distance_from_suburbs(self, uniqueId_loc_1, uniqueId_loc_2):
        """
        Returns the distance between two locations in kilometers.
        """
        lat_1 = self.locations[uniqueId_loc_1].latitude
        lon_1 = self.locations[uniqueId_loc_1].longitude
        lat_2 = self.locations[uniqueId_loc_2].latitude
        lon_2 = self.locations[uniqueId_loc_2].longitude
        return calc_distance_from_coordinates(lat_1, lon_1, lat_2, lon_2)
        
    def draw_location_of_residency(self):
        """
        Returns the uniqueId of a location which was drawn at random with
        suburbs exhibiting a higher population having higher chances to be
        drawn.
        """
        rnd = random.randint(0, self.total_population - 1)
        last_pop_step = 0
        for uniqueId in self.acc_population.keys():
            if last_pop_step <= rnd and rnd < self.acc_population[uniqueId]:
                return uniqueId
            last_pop_step = self.acc_population[uniqueId]
    
    def draw_location_of_employment(self, loc_of_residency_id):
        """
        Returns the unique Id of a location which was drawn at random based on
        the location of residency and the average commute from this suburb.
        """
        mean = self.locations[loc_of_residency_id].commute_mean
        std_dev = self.locations[loc_of_residency_id].commute_std_dev
        distance_work_residency = -1
        while distance_work_residency < 0: 
            distance_work_residency = np.random.normal(mean, std_dev)
        
        min_diff, min_diff_id = -1, -1
        for unique_id in self.locations.keys():
            diff = abs(distance_work_residency - \
                       self.calc_distance_from_suburbs(loc_of_residency_id,
                                                       unique_id))
            if min_diff_id == -1 or min_diff > diff:
                min_diff = diff
                min_diff_id = unique_id
        return min_diff_id
    
    def relative_position(self, uniqueId):
        """
        Returns the locations position relative to the minimum latitude and
        longitude between all loaded location.
        """
        x = self.locations[uniqueId].longitude - self.min_lon
        y = self.locations[uniqueId].latitude - self.min_lat
        return np.array((x, y))
        
    def print_locations(self):
        """
        Prints all loaded locations in a readable format.
        """
        strUniqueId, strName, strPopulation, strLatitude, strLongitude = \
            "Id", "Name", "Population", "Latitude", "Longitude"
        strCommuteMean, strCommuteStdDev = "Commute mean", "Commute std dev"
        lenUniqueId, lenName, lenPopulation, lenLatitude, lenLongitude = \
            len(strUniqueId), len(strName), len(strPopulation), \
                len(strLatitude), len(strLongitude)
        lenCommuteMean, lenCommuteStdDev = len(strCommuteMean), \
            len(strCommuteStdDev)
        for loc in self.locations.values():
            lenUniqueId = max(lenUniqueId, len(str(loc.uniqueId)))
            lenName = max(lenName, len(loc.name))
            lenPopulation = max(lenPopulation, len(str(loc.population)))
            lenLatitude = max(lenLatitude, len(str(loc.latitude)))
            lenLongitude = max(lenLongitude, len(str(loc.longitude)))
            lenCommuteMean = max(lenCommuteMean, len(str(loc.commute_mean)))
            lenCommuteStdDev = max(lenCommuteStdDev,
                                   len(str(loc.commute_std_dev)))
        
        separator = " | "
        
        print(strUniqueId.rjust(lenUniqueId), end=separator)
        print(strName.rjust(lenName), end=separator)
        print(strPopulation.rjust(lenPopulation), end=separator)
        print(strLatitude.rjust(lenLatitude), end=separator)
        print(strLongitude.rjust(lenLongitude), end=separator)
        print(strCommuteMean.rjust(lenCommuteMean), end=separator)
        print(strCommuteStdDev.rjust(lenCommuteStdDev))
        
        for loc in self.locations.values():
            print(str(loc.uniqueId).rjust(lenUniqueId), end=separator)
            print(loc.name.rjust(lenName), end=separator)
            print(str(loc.population).rjust(lenPopulation), end=separator)
            print(str(loc.latitude).rjust(lenLatitude), end=separator)
            print(str(loc.longitude).rjust(lenLongitude), end=separator)
            print(str(loc.commute_mean).rjust(lenCommuteMean), end=separator)
            print(str(loc.commute_std_dev).rjust(lenCommuteStdDev))
            
    def __repr__(self):
        msg = ""
        if self.is_defined:
            msg = "Number of Locations: " + str(len(self.locations)) + "\n"
            msg += "Latitude:   [" + str(self.min_lat) + " <-- " + \
                  str(self.north_south_spread) + " --> " + \
                  str(self.max_lat) + "]\n" 
            msg += "Longitude:  [" + str(self.min_lon) + " <-- " + \
                   str(self.east_west_spread) + " --> " + \
                   str(self.max_lon) + "]\n"
            msg += "Population: " + str(self.total_population)
        else:
            msg = "Location Manager is not yet defined."
        
        return msg