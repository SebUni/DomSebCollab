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
        self.wm = WhereaboutsManager(self.lrm, self.clock)
        self.cp = CalendarPlanner(self.parameters, self.clock, self.lrm)
        self.hcm = HouseConsumptionManager(self.clock)
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
        
        self.extracted_lon = []
        self.extracted_lat = []
        self.extracted_soc = []
        
        # create agents
        self.co.t_print("Start to create agents")
        for agent_uid in range (self.num_agents):
            residency_location = self.lrm.draw_location_of_residency()
            employment_location = residency_location
            while employment_location == residency_location:
                employment_location = \
                    self.lrm.draw_location_of_employment(residency_location)
            company = self.cpm.add_employee_to_location(employment_location)
            
            #TODO reconsider if agents should all start at home
            cur_location = residency_location 
            pos = self.lrm.relative_location_position(cur_location)
            
            house_agent = HouseAgent(agent_uid, self, self.clock,
                                     residency_location, company, self.chm,
                                     self.epm, self.hcm, self.hgm)
            car_agent = CarAgent(agent_uid, self, self.clock, cur_location,
                                 house_agent, company, self.lrm, self.cmm,
                                 self.wm, self.cp, self.parameters)
            self.schedule_houses.add(house_agent)
            self.schedule_cars.add(car_agent)
            self.space.place_agent(car_agent, pos)
            self.extracted_lon.append([])
            self.extracted_lat.append([])
            self.extracted_soc.append([])
        
        self.co.t_print("Agent creation complete")
        self.co.t_print("INITIALISATION COMPLETE")
        self.co.t_print("")
        self.co.t_print("COMMENCING STEP CALCULATION")
        
    def step(self):
        '''Advance the model by one step.'''
        self.co.t_print("Now calculating time step #" \
                        + str(self.clock.cur_time_step))
        self.clock.step()
        self.hcm.step()
        self.hgm.step()
        self.wm.prepare_movement()
        self.schedule_houses.step()
        self.schedule_cars.step()
        
        for i, car_agent in enumerate(self.schedule_cars.agents):
            self.extracted_lon[i].append(car_agent.pos[0])
            self.extracted_lat[i].append(car_agent.pos[1])
            cur_soc = car_agent.soc / car_agent.car_model.battery_capacity
            self.extracted_soc[i].append(cur_soc)
            
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
                
            