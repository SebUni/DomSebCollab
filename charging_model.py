# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 17:46:52 2020

@author: S3739258
"""

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace

from clock import Clock
from car_agent import CarAgent
from house_agent import HouseAgent
from location_road_manager import LocationRoadManager
from whereabouts_manager import WhereaboutsManager
from car_model_manager import CarModelManager
from charger_manager import ChargerManager
from electricity_plan_manager import ElectricityPlanManager
from company_manager import CompanyManager
from calendar_planner import CalendarPlanner

class ChargingModel(Model):
    """The charging model with N agents."""
    def __init__(self, nbr_of_agents, time_step):
        self.num_agents = nbr_of_agents
        self.clock = Clock(time_step) # time step in minutes
        self.elapsed_time = 0
        
        self.cmm = CarModelManager()
        self.chm = ChargerManager()
        self.epm = ElectricityPlanManager(time_step)
        self.cpm = CompanyManager(self.clock, self.chm, self.epm)
        self.lrm = LocationRoadManager()
        self.wm = WhereaboutsManager(self.lrm, time_step)
        self.cp = CalendarPlanner(self.clock, self.lrm)
        self.schedule_cars = RandomActivation(self)
        self.schedule_houses = RandomActivation(self)
        # extra promil is needed as east_west_spread and north_south_spread
        # are OPEN interval limits and agents can not be placed on this border
        # point
        self.space = ContinuousSpace(self.lrm.east_west_spread * 1.001,
                                     self.lrm.north_south_spread * 1.001,
                                     False)
        # create agents
        for agent_uid in range (self.num_agents):
            residency_location = self.lrm.draw_location_of_residency()
            #TODO reconsider if agents should all start at home
            cur_location = residency_location 
            pos = self.lrm.relative_location_position(cur_location)
            house_agent = HouseAgent(agent_uid, self, self.clock,
                                     residency_location, self.chm, self.epm)
            employment_location = \
                self.lrm.draw_location_of_employment(residency_location)
            company = self.cpm.add_employee_to_location(employment_location)
            calendar = self.cp.create_calendar(residency_location,
                                               employment_location)
            # the following three conditions are explained in car_agent.py
            departure_condition = "ONE_WAY_TRIP"
            reserve_range = 10
            queuing_condition = "WHEN_NEEDED"
            car_agent = CarAgent(agent_uid, self, self.clock, cur_location,
                                 house_agent, company, self.lrm, self.cmm,
                                 self.wm, calendar, departure_condition,
                                 reserve_range, queuing_condition)
            self.schedule_houses.add(house_agent)
            self.schedule_cars.add(car_agent)
            self.space.place_agent(car_agent, pos)
        
    def step(self):
        '''Advance the model by one step.'''
        self.clock.step()
        self.wm.prepare_movement()
        self.schedule_houses.step()
        self.schedule_cars.step()
        
        