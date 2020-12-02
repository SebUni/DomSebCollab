# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 17:46:52 2020

@author: S3739258
"""

from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace
from mesa.datacollection import DataCollector

from location_manager import LocationManager
from whereabouts_manager import WhereaboutsManager

class CarAgent(Agent):
    """An agent with fixed initial wealth."""
    def __init__(self, agent_uid, model, residency_location_uid,
                 employment_location_uid):
        super().__init__(agent_uid, model)
        self.residency_location_uid = residency_location_uid
        self.employment_location_uid = employment_location_uid
        
    def step(self):
        self.move()
        
    def move(self):
        new_position = self.model.wm.whereabouts[self.unique_id].cur_location_coordinates
        self.model.grid.move_agent(self, new_position)

class ChargingModel(Model):
    """The charging model with N agents."""
    def __init__(self, N):
        self.num_agents = N
        self.tick_per_time_step = 60 # reciprical of ticks-per-hour
        self.lm = LocationManager()
        self.lm.load_all()
        self.wm = WhereaboutsManager(self.lm, 10)
        self.schedule = RandomActivation(self)
        self.space = ContinuousSpace(self.lm.east_west_spread,
                                     self.lm.north_south_spread,
                                     False)
        
        print(str(self.lm.east_west_spread) + " / " + str(self.lm.north_south_spread))
        # create agents
        for agent_uid in range (self.num_agents):
            residency_location_uid = self.lm.draw_location_of_residency()
            employment_location_uid = \
                self.lm.draw_location_of_employment(residency_location_uid)
            cur_location_uid = residency_location_uid #TODO reconsider this
            pos = self.lm.relative_position(cur_location_uid)
            print(str(pos))
            self.wm.track_new_agent(agent_uid, cur_location_uid)
            a = CarAgent(agent_uid, self, residency_location_uid,
                         employment_location_uid)
            self.space.place_agent(a, pos)
            self.schedule.add(a)
    
        something = 0
        self.datacollector = DataCollector(
            model_reporters={"Something": something},
            agent_reporters={"Something": "something"})
    
    def step(self):
        '''Advance the model by one step.'''
        self.wm.elapse_one_tick()
        self.datacollector.collect(self)
        self.schedule.step()
        
        