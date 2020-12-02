# -*- coding: utf-8 -*-
"""
Created on Tue Dec  1 16:20:06 2020

@author: S3739258
"""

import networkx as nx    

class Whereabouts():
    """
    Provides information on the current position of the agent.
    
    This class calculates the progress of travels and feeds information on the
    geographic whereabouts of the agent to the charging model.
    """
    def __init__(self, start_location_uid, location_manager, tick_duration):
        self.cur_location_uid = start_location_uid
        self.cur_edge = (start_location_uid, start_location_uid)
        self.tick_duration = tick_duration
        self.lm = location_manager
        self.tn = self.lm.traffic_network
        self.cur_location_coordinates \
            = self.coordinates_from_location_uid(self.cur_location_uid)
        self.is_travelling = False
        self.distance_travelled = 0
        self.route = []
        
    def coordinates_from_location_uid(self, location_uid):
        x = self.lm.locations[location_uid].longitude
        y = self.lm.locations[location_uid].latitude
        return [x,y]
        
    def set_destination(self, destination_location_uid):
        """
        Sets a new destination and calculates route to get there.
        """
        self.route = nx.shortest_path(self.tn, self.cur_location_uid,
                                      destination_location_uid, 'distance')
        self.is_travelling = True
    
    def elapse_one_time_step(self, velocity):
        if self.is_travelling == True:
            # adapt travel parameter
            self.distance_travelled += velocity * self.tick_duration
            # determine current road
            sum_dist_to_prev_node = 0.0
            sum_dist_to_cur_node = 0.0
            prev_node = self.route[0]
            cur_node = self.route[0]
            for cn in self.route:
                cur_node = cn
                if cur_node == prev_node: continue
                sum_dist_to_cur_node += self.tn[prev_node][cur_node]['distance']
                if sum_dist_to_cur_node > self.distance_travelled:
                    break
                prev_node = cur_node;
                sum_dist_to_prev_node = sum_dist_to_cur_node
                
            self.cur_edge = (prev_node, cur_node)
            if prev_node == cur_node:      # this case only applies once the \
                self.route = []            # agent arrived at its destionation
                self.distance_travelled = 0
                self.is_travelling = False
                self.cur_location_uid = cur_node
                self.cur_location_coordinates \
                    = self.coordinates_from_location_uid(cur_node)
            else:
                self.cur_location_uid = prev_node
                coord_prev_node = self.coordinates_from_location_uid(prev_node)
                coord_cur_node = self.coordinates_from_location_uid(cur_node)
                dist_trvld_on_cur_edge \
                    = self.distance_travelled - sum_dist_to_prev_node
                ratio_trvld_on_cur_edge = dist_trvld_on_cur_edge \
                            / (sum_dist_to_cur_node - sum_dist_to_prev_node)
                diff_vct = [coord_cur_node[0] - coord_prev_node[0],
                            coord_cur_node[1] - coord_prev_node[1]]
                self.cur_location_coordinates = \
                    [coord_prev_node[0] + ratio_trvld_on_cur_edge * diff_vct[0],
                     coord_prev_node[1] + ratio_trvld_on_cur_edge * diff_vct[1]]
    
    def __repr__(self):
        msg = "Current location Uid: " + str(self.cur_location_uid) + "\n"
        msg += "Current edge: " + str(self.cur_edge) + "\n"
        msg += "Tick duration: " + str(self.tick_duration) + "\n"
        msg += "Current coordinates: "
        msg += str(self.cur_location_coordinates[0]) + " "
        msg += str(self.cur_location_coordinates[1]) + "\n"
        msg += "Is traveling: " + str(self.is_travelling) + "\n"
        msg += "Distance travelled: " + str(self.distance_travelled) + "\n"
        msg += "Route: " + str(self.route)
        return msg