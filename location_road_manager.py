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
    def __init__(self, parameters, company_manager, clock, extracted_data):
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
        self.commutes = {}
        self.parameters = parameters
        self.cpm = company_manager
        self.clock = clock
        self.traffic_jam_velocity \
            = self.parameters.get("traffic_jam_velocity","float")
        self.k_jam = self.parameters.get("k_jam","float")
        self.pcu_length = self.parameters.get("pcu_length","float")
        self.inner_area_speed_limit \
            = self.parameters.get("inner_area_speed_limit","float")
        self.extracted_data = extracted_data
        
        self.load_locations()
        self.load_connections()
        self.load_commutes()
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
        travel_time_in_h = 0
        start_node = -1
        start_node_defined = False
        for end_node in route:
            if start_node_defined:
                distance = \
                    self.traffic_network[start_node][end_node]['distance']
                speed_limit = \
                    self.traffic_network[start_node][end_node]['speed_limit']
                travel_time_in_h += distance / speed_limit
                
            start_node = end_node
            start_node_defined = True
        
        return travel_time_in_h * 60
    
    def load_locations(self):
        """
        Reads information on individual suburbs from locations.csv.
        """
        cast = Cast("Location")
        sa_level = self.parameters.get("sa_level","int")
        self.locations = {}
        csv_helper = CSVHelper("data/SA" + str(sa_level),"locations.csv")
        for row in csv_helper.data:
            uid = cast.to_positive_int(row[0], "Uid")
            cast.uid = uid
            name = row[1]
            longitude = cast.to_float(row[2], "Longitude")
            latitude = cast.to_float(row[3], "Latitude")
            occupant_distribution \
                = cast.to_positive_int_list(row[4], "Occupant distribution")
            occupant_values \
                = cast.to_positive_int_list(row[5], "Occupant values")
            pv_density \
                = cast.to_positive_float(row[6], "PV density")
            pv_avg_capacity \
                = cast.to_positive_float(row[7], "PV average capacity")
            distance_commuted_if_work_and_home_equal_distribution \
                = cast.to_positive_int_list(row[8], "Distance distribution")
            distance_commuted_if_work_and_home_equal_values \
                = cast.to_positive_float_list(row[9], "Distance values")
            flats_total = cast.to_positive_int(row[10], "Flats total")
            houses_owned = cast.to_positive_int(row[11], "Houses owned")
            houses_total = cast.to_positive_int(row[12], "Houses total")
            
            tracking_id = self.extracted_data.init_tracked_agent(uid)
            loc = Location(uid, name, tracking_id, longitude, latitude,
                         occupant_distribution, occupant_values,
                         pv_density, pv_avg_capacity,
                         distance_commuted_if_work_and_home_equal_distribution,
                         distance_commuted_if_work_and_home_equal_values,
                         flats_total, houses_owned, houses_total,
                         self.extracted_data)
            # add public charger
            self.cpm.add_company(loc)
            
            self.locations[loc.uid] = loc
        
    def load_connections(self):
        """
        Reads information on suburb connection from connections.csv.
        """
        cast = Cast("Connection")
        sa_level = self.parameters.get("sa_level","int")
        self.traffic_network = nx.DiGraph()
        # add locations
        for location in self.locations.values():
            self.traffic_network.add_node(location.uid)
        # add edges
        csv_helper = CSVHelper("data/SA" + str(sa_level),"connections.csv")
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
            speed_lmt = cast.to_positive_int(row[2], "Speed limit")
            nbr_of_lns = cast.to_positive_int(row[3], "Number of lanes")
                
            self.traffic_network.add_edge(start_location.uid, end_location.uid,
                                          distance=flt_dist,
                                          speed_limit=speed_lmt,
                                          current_velocity=speed_lmt,
                                          number_of_lanes=nbr_of_lns)
            self.traffic_network.add_edge(end_location.uid, start_location.uid,
                                          distance=flt_dist,
                                          speed_limit=speed_lmt,
                                          current_velocity=speed_lmt,
                                          number_of_lanes=nbr_of_lns)
            
    def load_commutes(self):
        cast = Cast("Commutes")
        sa_level = self.parameters.get("sa_level","int")
        self.commutes = dict()
        work_locations = dict()
        csv_helper = CSVHelper("data/SA" + str(sa_level),"commutes.csv",False)
        for i, row in enumerate(csv_helper.data):
            # determine possible work location
            if i == 0:
                for j, col in enumerate(row[1:]):
                    work_locations[j+1] \
                        = self.locations[cast.to_positive_int(col,
                                                              "Work location")]
            else:
                abs_commutes = dict()
                residency_location \
                    = self.locations[cast.to_positive_int(row[0],
                                                         "Residency location")]
                for j, col in enumerate(row[1:]):
                    abs_commutes[work_locations[j+1]] \
                        = cast.to_positive_int(col, "Commute Amount")
                total_workers_at_res_loc = sum(abs_commutes.values())
                self.commutes[residency_location] = dict()
                for work_location, abs_commute in abs_commutes.items():
                    self.commutes[residency_location][work_location] \
                        = abs_commute / total_workers_at_res_loc
                residency_location.population = total_workers_at_res_loc
    
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
        location_of_employment = None
        rnd = random.random()
        sum_rel_commutes = 0
        for work_location, rel_commute in self.commutes[residency_location].items():
            sum_rel_commutes += rel_commute
            location_of_employment = work_location
            if sum_rel_commutes >= rnd:
                break
        
        #return list(self.locations.values())[0]
        return location_of_employment
    
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
    
    def determine_current_velocity_on_edges(self, agents_on_edges):
        for edge in list(self.traffic_network.edges):
            K = self.traffic_network.edges[edge]['distance']
            N = agents_on_edges[edge]
            v_lim = self.traffic_network.edges[edge]['speed_limit']
            nbr_of_lanes = self.traffic_network.edges[edge]['number_of_lanes']
            cur_speed_flow = self.traffic_network.edges[edge]['speed_limit']
            if N != 0:
                cur_speed_flow = (K/N) \
                    * ((1000 * v_lim * nbr_of_lanes)/(self.pcu_length + 2 * v_lim))\
                    * ((N / K - self.k_jam)/((1/(self.pcu_length + 2 * v_lim)) - self.k_jam))
            
            self.traffic_network.edges[edge]['cur_speed'] \
                = max(min(cur_speed_flow, \
                      self.traffic_network.edges[edge]['speed_limit']),
                      self.traffic_jam_velocity)
    
    def step(self):
        for location in self.locations.values():
            location.step()
        
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