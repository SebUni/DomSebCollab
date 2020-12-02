# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 17:46:52 2020

@author: S3739258
"""

from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace
from mesa.datacollection import DataCollector

import networkx as nx

from location_manager import LocationManager

def load_traffic_network(location_manager):
    tn = nx.Graph()
    for location in location_manager.locations.values():
        tn.add_node(location.unique_id)
    for start_node in location_manager.connections.keys():
        for end_node in location_manager.connections[start_node]:
            if start_node < end_node:
                tn.add_edge(start_node, end_node)
    return tn

class CarAgent(Agent):
    pass

class ChargingModel(Model):
    """The charging model with N agents."""
    def __init__(self, N):
        self.num_agents = N
        self.lm = LocationManager()
        self.lm.load_all()
        self.tn = load_traffic_network(self.lm);
        self.schedule = RandomActivation(self)
        self.space = ContinuousSpace(self.lm.east_west_spread,
                                     self.lm.north_south_spread,
                                     False, grid_width=10, grid_height=10)
        # create agents
        for i in range (self.num_agents):
            residency_location_id = self.lm.draw_location_of_residency()
            employment_location_id = \
                self.lm.draw_location_of_employment(residency_location_id)
            pos = self.lm.relative_position(residency_location_id)
            a = CarAgent(i, self, pos, residency_location_id,
                         employment_location_id)
            self.space.place_agent(a, pos)
            self.schedule.add(a)
            
            # TODO add to grid / see money agent model
    
        something = 0
        self.datacollector = DataCollector(
            model_reporters={"Something": something},
            agent_reporters={"Something": "something"})
    
    def step(self):
        '''Advance the model by one step.'''
        self.datacollector.collect(self)
        self.schedule.step()
        
        