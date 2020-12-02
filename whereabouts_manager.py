# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 10:57:16 2020

@author: S3739258
"""

import whereabouts as Whereabouts
import location_manager as LocationManager
import traffic_network as TrafficNetwork

class WhereaboutsManager():
    """
    Managaes the individual Whereabouts.
    
    This class is implement to simplify the interaction between all
    Whereabouts-classes.
    """
    def __init__(self, location_manager, traffic_network, tick_per_time_step):
        self.lm = location_manager
        self.tn = traffic_network
        self.tick_per_time_step = tick_per_time_step
        self.whereabouts = dict()
        
    def add_whereabouts(self, agent_uid):
        """ Adds tracking of a new agent to the manager. """
        self.whereabouts[agent_uid] \
            = Whereabouts(agent_uid, self.lm, self.tick_duration, self.tn)
    
    def count_agents_on_edges(self):
        """ Counts how many agents are on each edge.
        
        Needed to estimate congestions and calculate agents velocity."""
        pass
    
    def set_destination(self, agent_uid, destination_location_uid):
        """ Sets a new destination for an agent incl. route determination. """
        self.whereabouts[agent_uid].set_destination(destination_location_uid)
    
    def elapse_one_time_step(self):
        """ Lets agents move for one time step.
        
        This function calls the elapse_one_tick function for a given number of
        times as defined in time_step_duration. The idea is that time steps
        can be chosen coarser without traffic being calculated inapproproately. 
        """
        for t in range(self.tick_per_time_step):
            self.elapse_one_tick()
    
    def elapse_one_tick(self):
        """ Lets agents move for one tick. 
        
        One tick is the smallest time unit calculated. """
        for wa_key in self.whereabouts.keys():
            velocity = 1 #TODO derive velocity from traffic congestion and data
            self.whereabouts[wa_key].elapse_one_tick(velocity)