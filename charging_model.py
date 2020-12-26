# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 17:46:52 2020

@author: S3739258
"""

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace
from mesa.datacollection import DataCollector

from clock import Clock
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
        self.clock = Clock(time_step) # time step in minutes
        self.elapsed_time = 0
        
        self.cmm = CarModelManager()
        self.chm = ChargerManager()
        self.epm = ElectricityPlanManager(time_step)
        self.cpm = CompanyManager(self.chm, self.epm, self.clock)
        self.lrm = LocationRoadManager()
        self.wm = WhereaboutsManager(self.lrm, time_step)
        self.schedule_cars = RandomActivation(self)
        self.schedule_houses = RandomActivation(self)
        self.space = ContinuousSpace(self.lrm.east_west_spread,
                                     self.lrm.north_south_spread,
                                     False)
        # create agents
        for agent_uid in range (self.num_agents):
            residency_location = self.lrm.draw_location_of_residency()
            #TODO reconsider if agents should all start at home
            cur_location = residency_location 
            pos = self.lrm.relative_position(cur_location)
            house_agent = HouseAgent(agent_uid, self, self.clock,
                                     residency_location, self.chm, self.epm)
            employment_location = \
                self.lrm.draw_location_of_employment(residency_location)
            company = self.cpm.add_employee_to_location(employment_location)
            car_agent = CarAgent(agent_uid, self, cur_location, house_agent,
                                 company, self.cmm, self.wm)
            self.schedule_houses.add(house_agent)
            self.schedule_cars.add(car_agent)
            self.space.place_agent(car_agent, pos)
    
        something = 0
        self.datacollector = DataCollector(
            model_reporters={"Something": something},
            agent_reporters={"Something": "something"})
    
    def step(self):
        '''Advance the model by one step.'''
        self.wm.prepare_movement()
        self.schedule.step()
        self.datacollector.collect(self)
        
        