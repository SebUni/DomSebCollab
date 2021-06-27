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
    def __init__(self, location_road_manager, clock):
        """
        Initialises the whereabouts manager, which keeps track of agents
        journeys.

        Parameters
        ----------
        location_road_manager : LocationRoadManager
            Handle to the location road manager.
        clock: Clock
            The instance of the clock module that provides information on time.
        Returns
        -------
        None.
        """
        self.lrm = location_road_manager
        self.whereabouts = dict()
        self.time_step = clock.time_step
        
    def track_new_agent(self, agent_uid, cur_location):
        """ Adds tracking of a new agent to the manager. """
        self.whereabouts[agent_uid] \
            = whereabouts.Whereabouts(agent_uid, cur_location, self.lrm,
                                      self.time_step)
        return self.whereabouts[agent_uid]
    
    def count_agents_on_edges(self):
        """ Counts how many agents are on each edge.
        
        Needed to estimate congestions and calculate agents velocity."""
        agents_on_edge = dict()
        for edge in list(self.lrm.traffic_network.edges):
            count = 0
            for whereabouts_it in self.whereabouts.values():
                if whereabouts_it.cur_edge == edge:
                    count += 1
            agents_on_edge[edge] = count
        
        return agents_on_edge
    
    def prepare_movement(self):
        """ Determines all parameters, especially the velocity, required by
        Agents to calculate their next movement. """
        agents_on_edges = self.count_agents_on_edges()
        self.lrm.determine_current_velocity_on_edges(agents_on_edges)