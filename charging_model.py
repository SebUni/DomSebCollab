# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 17:46:52 2020

@author: S3739258
"""

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace
from mesa.datacollection import DataCollector

from car_agent import CarAgent
from house_agent import HouseAgent
from location_road_manager import LocationRoadManager
from whereabouts_manager import WhereaboutsManager
from car_model_manager import CarModelManager
from charger_manager import ChargerManager
from electricity_plan_manager import ElectricityPlanManager
from company_manager import CompanyManager

class ChargingModel(Model):
    """The charging model with N agents."""
    def __init__(self, nbr_of_agents, time_step):
        self.num_agents = nbr_of_agents
        self.time_step = time_step # time step in minutes
        
        self.cmm = CarModelManager()
        self.chm = ChargerManager()
        self.epm = ElectricityPlanManager(self.time_step)
        self.cpm = CompanyManager(self.chm, self.epm)
        self.lrm = LocationRoadManager()
        self.wm = WhereaboutsManager(self.lrm, self.time_step)
        self.schedule_cars = RandomActivation(self)
        self.schedule_houses = RandomActivation(self)
        self.space = ContinuousSpace(self.lrm.east_west_spread,
                                     self.lrm.north_south_spread,
                                     False)
        """
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
        """
    
    def step(self):
        '''Advance the model by one step.'''
        self.wm.elapse_one_time_step()
        self.datacollector.collect(self)
        self.schedule.step()
        
        