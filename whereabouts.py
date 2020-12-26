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
    def __init__(self, agent_uid, start_location, location_road_manager,
                 time_step):
        
        self.agent_uid = agent_uid
        self.lrm = location_road_manager
        self.time_step = time_step
        self.cur_location = start_location
        self.cur_edge = (start_location.uid, start_location.uid)
        self.cur_location_coordinates = self.cur_location.coordinates()
        self.is_travelling = False
        self.cur_velocity = 0 # in km/h
        self.distance_travelled = 0 # in km
        self.route = []
        
    def set_destination(self, destination_location):
        """
        Sets a new destination and calculates route to get there.
        """
        self.route = nx.shortest_path(self.lrm.traffic_network,
                                      self.cur_location.uid,
                                      destination_location.uid, 'distance')
        self.is_travelling = True
    
    def elapse_one_tick(self):
        if self.is_travelling == True:
            # adapt travel parameter
            self.distance_travelled += self.cur_velocity * self.time_step / 60
            # determine current road
            sum_dist_to_prev_node = 0.0
            sum_dist_to_cur_node = 0.0
            prev_node = self.route[0]
            cur_node = self.route[0]
            for cn in self.route:
                cur_node = cn
                if cur_node == prev_node: continue
                sum_dist_to_cur_node \
                    += self.lrm.traffic_network[prev_node][cur_node]['distance']
                if sum_dist_to_cur_node > self.distance_travelled:
                    break
                prev_node = cur_node;
                sum_dist_to_prev_node = sum_dist_to_cur_node
                
            self.cur_edge = (prev_node, cur_node)
            if prev_node == cur_node:      # this case only applies once the \
                self.route = []            # agent arrived at its destionation
                self.distance_travelled = 0
                self.is_travelling = False
                self.cur_location = self.lrm.locations[cur_node]
                self.cur_location_coordinates = self.cur_location.coordinates()
            else:
                self.cur_location = self.lrm.locations[prev_node]
                coord_prev_node = self.lrm.locations[prev_node].cooridnates()
                coord_cur_node = self.lrm.locations[cur_node].cooridnates()
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
        msg += "Time step duration: " + str(self.time_step_duration) + "\n"
        msg += "Current coordinates: "
        msg += str(self.cur_location_coordinates[0]) + " "
        msg += str(self.cur_location_coordinates[1]) + "\n"
        msg += "Is traveling: " + str(self.is_travelling) + "\n"
        msg += "Distance travelled: " + str(self.distance_travelled) + "\n"
        msg += "Route: " + str(self.route)
        return msg