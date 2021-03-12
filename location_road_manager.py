# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 23:28:13 2020

@author: S3739258
"""

import random
import sys
import numpy as np
import math
import networkx as nx

from cast import Cast
from csv_helper import CSVHelper

from location import Location

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

class LocationRoadManager():
    """
    Holds information on locations and how they interact.
    """
    def __init__(self, company_manager):
        self.min_lat = 90.0   # most southern point
        self.max_lat = -90.0  # most northern point
        self.min_lon = 361.0  # most western point
        self.max_lon = -1.0   # most eastern point
        self.east_west_spread = 0.0
        self.north_south_spread = 0.0
        self.total_population = 0
        self.acc_population = {}
        self.locations = {}
        self.traffic_network = nx.Graph()
        self.cpm = company_manager
        
        self.load_locations()
        self.load_connections()
        self.process_location_data()
    
    def direct_distance_between_locations(self, location_1, location_2):
        """
        Returns the distance between two locations in kilometers.
        """
        lon_1, lat_1 = location_1.longitude, location_1.latitude
        lon_2, lat_2 = location_2.longitude, location_2.latitude
        return calc_distance_from_coordinates(lat_1, lon_1, lat_2, lon_2)
    
    def estimated_travel_time_between_locations(self, location_1, location_2):
        """
        Returns the time needed to travel between two locations in minutes.
        """
        route = nx.shortest_path(self.traffic_network, location_1.uid,
                                 location_2.uid, 'distance')
        travel_time = 0
        start_node = -1
        start_node_defined = False
        for end_node in route:
            if start_node_defined:
                distance = \
                    self.traffic_network[start_node][end_node]['distance']
                speed_limit = \
                    self.traffic_network[start_node][end_node]['speed_limit']
                travel_time += distance / speed_limit
                
            start_node = end_node
            start_node_defined = True;
        
        return travel_time
    
    def load_locations(self):
        """
        Reads information on individual suburbs from locations.csv.
        """
        cast = Cast("Location")
        self.locations = {}
        csv_helper = CSVHelper("data","locations.csv")
        for row in csv_helper.data:
            uid = cast.to_positive_int(row[0], "Uid")
            cast.uid = uid
            name = row[2]
            longitude = cast.to_float(row[3], "Longitude")
            latitude = cast.to_float(row[4], "Latitude")
            population = cast.to_positive_int(row[5], "Population")
            commute_mean = cast.to_positive_float(row[6], "Commute mean")
            commute_std_dev = cast.to_positive_float(row[7], "Commute std dev")
            occupant_distribution \
                = cast.to_positive_int_list(row[8], "Occupant distribution")
            occupant_values \
                = cast.to_positive_int_list(row[9], "Occupant values")
            pv_capacity_mean \
                = cast.to_positive_float(row[10], "PV capacity mean")
            pv_capacity_std_dev \
                = cast.to_positive_float(row[11], "PV capacity std dev")
            battery_capacity_mean \
                = cast.to_positive_float(row[12], "Battery capacity mean")
            battery_capacity_std_dev\
                = cast.to_positive_float(row[13], "Battery capacity std dev")
                    
            loc = Location(uid, name, longitude, latitude, population,
                           commute_mean, commute_std_dev,
                           occupant_distribution, occupant_values,
                           pv_capacity_mean, pv_capacity_std_dev,
                           battery_capacity_mean, battery_capacity_std_dev)
            # add public charger
            self.cpm.add_company(loc)
            
            self.locations[loc.uid] = loc
            
        
    def load_connections(self):
        """
        Reads information on suburb connection from connections.csv.
        """
        cast = Cast("Connection")
        self.traffic_network = nx.Graph()
        # add locations
        for location in self.locations.values():
            self.traffic_network.add_node(location.uid)
        # add edges
        csv_helper = CSVHelper("data","connections.csv")
        for row in csv_helper.data:
            try:
                start_location_uid = int(row[0])
                start_location = self.locations[start_location_uid]
                end_location_uid = int(row[1])
                end_location = self.locations[end_location_uid]
            except ValueError:
                sys.exit("Connection not well defined for " + row[0] + " - " \
                         + row[1] + ".")
            flt_dist = self.direct_distance_between_locations(start_location,
                                                              end_location)
            speed_lmt = cast.to_positive_float(row[2], "Speed limit")
            # TODO incorperate conversion of Dom's road levels to speed_lmt
            speed_lmt = 50 # in km/h
                
            self.traffic_network.add_edge(start_location.uid, end_location.uid,
                                          distance=flt_dist,
                                          speed_limit=speed_lmt,
                                          current_velocity=speed_lmt)
            self.traffic_network.add_edge(end_location.uid, start_location.uid,
                                          distance=flt_dist,
                                          speed_limit=speed_lmt,
                                          current_velocity=speed_lmt)
    
    def process_location_data(self):
        """
        Calculates parameters summarising location data.
        """
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
            self.acc_population[loc] = self.total_population
        
        self.north_south_spread = round(self.max_lat - self.min_lat, 10)
        self.east_west_spread = round(self.max_lon - self.min_lon, 10)
        
    def draw_location_of_residency(self):
        """
        Returns a location which was drawn at random with suburbs exhibiting a
        higher population having higher chances to be drawn.
        """
        rnd = random.randint(0, self.total_population - 1)
        last_pop_step = 0
        for location in self.acc_population.keys():
            if last_pop_step <= rnd and rnd < self.acc_population[location]:
                return location
            last_pop_step = self.acc_population[location]
    
    def draw_location_of_employment(self, residency_location):
        """
        Returns a location which was drawn at random based on the location of
        residency and the average commute from this suburb.
        """
        distance_work_residency = residency_location.draw_commute_at_random()
        min_diff = -1
        min_diff_location = residency_location
        for location in self.locations.values():    
            diff = abs(distance_work_residency - \
                       self.direct_distance_between_locations(residency_location,
                                                       location))
            if min_diff == -1 or min_diff > diff:
                min_diff = diff
                min_diff_location = location
        return min_diff_location
    
    def relative_location_position(self, location):
        """
        Returns the location's position relative to the minimum latitude and
        longitude between all loaded location.

        Parameters
        ----------
        location : Location
            Well it's a location type object you wanna chuck in.

        Returns
        -------
        np.array
            The coordinate relative to the lower left-hand corner of the rect-
            angle enclosing all locations.

        """
        x = location.longitude - self.min_lon
        y = location.latitude - self.min_lat
        return np.array((x, y))
    
    def relative_coordinate_position(self, coordinates):
        """
        Returns the coordinates relative to the minimum latitude and
        longitude between all loaded location.
        """
        x = coordinates[0] - self.min_lon
        y = coordinates[1] - self.min_lat
        return np.array((x, y))
    
    def calc_route(self, start, destination):
        """
        Returns the shorts route from the start location to the end location.

        Parameters
        ----------
        start : Location
            Start location.
        destination : Location
            End location.

        Returns
        -------
        route : int[].
            A list with all location_uids to travel along.
        """
        return nx.shortest_path(self.traffic_network, start.uid,
                                destination.uid, 'distance')
    
    def calc_route_length(self, route):
        distance = 0
        start_node, start_node_defined = -1, False
        for end_node in route:
            if start_node_defined:
                distance = distance + \
                    self.traffic_network[start_node][end_node]['distance']
                
            start_node, start_node_defined = end_node, True
        
        return distance
            
        
    def print_locations(self):
        """
        Prints all loaded locations in a readable format.
        """
        str_uid, str_name, str_population, str_latitude, str_longitude =\
            "Id", "Name", "Population", "Latitude", "Longitude"
        str_commute_mean, str_commute_std_dev = \
            "Commute mean", "Commute std dev"
        len_uid, len_name, len_population, len_latitude, len_longitude =\
            len(str_uid), len(str_name), len(str_population), \
                len(str_latitude), len(str_longitude)
        len_commute_mean, len_commute_std_dev = len(str_commute_mean), \
            len(str_commute_std_dev)
        for loc in self.locations.values():
            len_uid = max(len_uid, len(str(loc.uid)))
            len_name = max(len_name, len(loc.name))
            len_population = max(len_population, len(str(loc.population)))
            len_latitude = max(len_latitude, len(str(loc.latitude)))
            len_longitude = max(len_longitude, len(str(loc.longitude)))
            len_commute_mean = max(len_commute_mean,
                                   len(str(loc.commute_mean)))
            len_commute_std_dev = max(len_commute_std_dev,
                                   len(str(loc.commute_std_dev)))
        
        separator = " | "
        
        print(str_uid.rjust(len_uid), end=separator)
        print(str_name.rjust(len_name), end=separator)
        print(str_population.rjust(len_population), end=separator)
        print(str_latitude.rjust(len_latitude), end=separator)
        print(str_longitude.rjust(len_longitude), end=separator)
        print(str_commute_mean.rjust(len_commute_mean), end=separator)
        print(str_commute_std_dev.rjust(len_commute_std_dev))
        
        for loc in self.locations.values():
            print(str(loc.uid).rjust(len_uid), end=separator)
            print(loc.name.rjust(len_name), end=separator)
            print(str(loc.population).rjust(len_population), end=separator)
            print(str(loc.latitude).rjust(len_latitude), end=separator)
            print(str(loc.longitude).rjust(len_longitude), end=separator)
            print(str(loc.commute_mean).rjust(len_commute_mean), end=separator)
            print(str(loc.commute_std_dev).rjust(len_commute_std_dev))
            
    def __repr__(self):
        msg = ""
        msg = "Number of Locations: " + str(len(self.locations)) + "\n"
        msg += "Latitude:   [" + str(self.min_lat) + " <-- " + \
                str(self.north_south_spread) + " --> " + \
                str(self.max_lat) + "]\n" 
        msg += "Longitude:  [" + str(self.min_lon) + " <-- " + \
                str(self.east_west_spread) + " --> " + \
                str(self.max_lon) + "]\n"
        msg += "Population: " + str(self.total_population)
        
        return msg