# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 10:57:16 2020

@author: S3739258
"""

import whereabouts

class WhereaboutsManager():
    """
    Managaes the individual Whereabouts.
    
    This class is implement to simplify the interaction between all
    Whereabouts-classes.
    """
    def __init__(self, location_road_manager, time_step):
        """
        Initialises the whereabouts manager, which keeps track of agents
        journeys.

        Parameters
        ----------
        location_road_manager : LocationRoadManager
            Handle to the location road manager.
        time_step : int
            Simulation time step in minutes.
        Returns
        -------
        None.
        """
        self.lrm = location_road_manager
        self.whereabouts = dict()
        self.time_step = time_step
        self.agents_on_edge = dict()
        
    def track_new_agent(self, agent_uid, cur_location):
        """ Adds tracking of a new agent to the manager. """
        self.whereabouts[agent_uid] \
            = whereabouts.Whereabouts(agent_uid, cur_location, self.lrm,
                                      self.time_step)
        return self.whereabouts[agent_uid]
    
    def count_agents_on_edges(self):
        """ Counts how many agents are on each edge.
        
        Needed to estimate congestions and calculate agents velocity."""
        self.agents_on_edge = dict()
        for edge in list(self.lm.traffic_network.edges):
            edge_inv = (edge[1], edge[0])
            count = 0
            for whereabouts_it in self.whereabouts.values():
                if whereabouts_it.cur_edge == edge or \
                    whereabouts_it.cur_edge == edge_inv:
                        count += 1
            self.agents_on_edge[edge] = count
    
    def elapse_one_time_step(self):
        """ Lets agents move for one time step.
        
        This function calls the elapse_one_tick function for a given number of
        times as defined in time_step_duration. The idea is that time steps
        can be chosen coarser without traffic being calculated inapproproately. 
        """
        for wa_key in self.whereabouts.keys():
            #TODO derive velocity from traffic congestion and data
            velocity = 1
            self.whereabouts[wa_key].elapse_one_tick(velocity)