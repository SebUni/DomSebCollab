# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 17:46:52 2020

@author: S3739258
"""

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace


from console_output import ConsoleOutput
from parameters import Parameters
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
from house_consumption_manager import HouseConsumptionManager
from house_generation_manager import HouseGenerationManager

class ChargingModel(Model):
    """The charging model with N agents."""
    def __init__(self, nbr_of_agents):
        self.co = ConsoleOutput()
        self.co.t_print("INITIALISING CHARGING MODEL")
        self.parameters = Parameters()
        self.num_agents = nbr_of_agents
        # time step and time step limit in minutes
        self.clock = Clock(self.parameters) 
        
        self.cmm = CarModelManager()
        self.chm = ChargerManager()
        self.epm = ElectricityPlanManager(self.parameters, self.clock)
        self.cpm = CompanyManager(self.parameters, self.clock, self.chm,
                                  self.epm)
        self.lrm = LocationRoadManager(self.parameters, self.cpm, self.clock)
        self.cp = CalendarPlanner(self.parameters, self.clock, self.lrm)
        self.wm = WhereaboutsManager(self.lrm, self.clock, self.cp)
        self.hcm = HouseConsumptionManager(self.clock, self.parameters)
        self.hgm = HouseGenerationManager(self.parameters, self.clock,
                                          self.epm, self.cmm)
        self.schedule_cars = RandomActivation(self)
        self.schedule_houses = RandomActivation(self)
        # extra promil is needed as east_west_spread and north_south_spread
        # are OPEN interval limits and agents can not be placed on this border
        # point
        self.space = ContinuousSpace(self.lrm.east_west_spread * 1.001,
                                     self.lrm.north_south_spread * 1.001,
                                     False)
        
        self.extracted_soc = []
        self.extracted_data = dict()
        
        # create agents
        self.co.t_print("Start to create agents")
        for agent_uid in range (self.num_agents):
            residency_location = self.lrm.draw_location_of_residency()
            employment_location = \
                self.lrm.draw_location_of_employment(residency_location)
            company = self.cpm.add_employee_to_location(employment_location)
            
            #TODO reconsider if agents should all start at home
            cur_activity = self.cp.HOME
            cur_location = residency_location 
            pos = self.lrm.relative_location_position(cur_location)
            
            house_agent = HouseAgent(agent_uid, self, self.clock,
                                     residency_location, company, self.chm,
                                     self.epm, self.hcm, self.hgm,
                                     self.parameters)
            car_agent = CarAgent(agent_uid, self, self.clock, cur_activity,
                                 cur_location, house_agent, company, self.lrm,
                                 self.cmm, self.wm, self.cp, self.parameters)
            self.schedule_houses.add(house_agent)
            self.schedule_cars.add(car_agent)
            self.space.place_agent(car_agent, pos)
        
        self.co.t_print("Agent creation complete")
        self.co.t_print("Create agent's work schedule")
        self.cp.prepare_schedule_generation()
        for car_agent in self.schedule_cars.agents:
            car_agent.generate_calendar_entries()
        self.co.t_print("Completed agent's work schedule")
        self.co.t_print("Agent creation complete")
        self.co.t_print("INITIALISATION COMPLETE")
        self.co.t_print("")
        self.co.t_print("COMMENCING STEP CALCULATION")
        
    def step(self):
        '''Advance the model by one step.'''
        self.co.t_print("Now calculating time step #" \
                        + str(self.clock.cur_time_step))
        self.clock.step()
        if self.clock.cur_time_step == 2300:
            test = 1
        self.hcm.step()
        self.hgm.step()
        self.wm.prepare_movement()
        self.schedule_houses.step()
        self.schedule_cars.step()
        for house_agent in self.schedule_houses.agents:
            house_agent.step_late()
        
        self.extracted_data[self.clock.elapsed_time] = dict()
        for car_agent in self.schedule_cars.agents:
            self.extracted_data[self.clock.elapsed_time][car_agent.uid] \
                = car_agent.extracted_data
            
    def summarise_simulation(self):
        self.co.t_print("STEP CALCULATION COMPLETE")
        self.co.t_print("")
        self.co.t_print("Summary")
        
        flat_cars = []
        for car_agent in self.schedule_cars.agents:
            if car_agent.would_run_flat == True:
                flat_cars.append(car_agent.uid)
        if len(flat_cars) == 0:
            self.co.t_print("Cars that would run flat: None")
        else:
            self.co.t_print("Cars that would run flat:" + str(flat_cars))
                
            