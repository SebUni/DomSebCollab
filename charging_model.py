# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 17:46:52 2020

@author: S3739258
"""

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace

import os
import psutil

from clock import Clock
from extracted_data import ExtractedData
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
from charging_strategy import ChargingStrategy

def get_current_ram_usage():
    process = psutil.Process(os.getpid())
    mem = process.memory_info()[0] / float(2 ** 30)
    vmem = process.memory_info()[1] / float(2 ** 30)
    return "RAM: {:.03f} GB / VRAM {:.03f} GB".format(mem, vmem)

class ChargingModel(Model):
    """The charging model with N agents."""
    def __init__(self, nbr_of_agents, console_output, parameters):
        self.co = console_output
        self.co.t_print("INITIALISING CHARGING MODEL")
        self.parameters = parameters
        self.num_agents = nbr_of_agents
        # time step and time step limit in minutes
        self.clock = Clock(self.parameters)
        self.chm = ChargerManager()
        self.epm = ElectricityPlanManager(self.parameters, self.clock)
        # create company manager
        self.extracted_company_data = ExtractedData(self.clock)
        self.extracted_company_data.init_tracked_var("Charger utilisation", 0)
        self.cpm = CompanyManager(self.parameters, self.clock, self.chm,
                                  self.epm, self.extracted_company_data)
        self.lrm = LocationRoadManager(self.parameters, self.cpm, self.clock)
        self.cmm = CarModelManager(self.parameters, self.lrm)
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
        
        msg="Selected number of agents: {}, season: {}, time step: {} min"
        self.co.t_print(msg.format(nbr_of_agents,
                                   self.clock.season_names[self.clock.season],
                                   self.clock.time_step))
        msg="Selected charging strategy: {}"
        cs = ChargingStrategy(parameters)
        self.co.t_print(msg.format(cs.charging_model_names[cs.charging_model]))
        msg = "Selected work charge price: {:.02f} $/kWh, " \
            + "employees per charger: {}"
        self.co.t_print(msg.format(\
            parameters.get("company_charger_cost_per_kWh", "float"),
            parameters.get("employees_per_charger", "int")))
        
        del msg, cs
        
        # create agents
        self.extracted_car_data = ExtractedData(self.clock)
        self.extracted_car_data.init_tracked_var("cur_activity", 0)
        self.extracted_car_data.init_tracked_var("charge_received_pv", 0)
        self.extracted_car_data.init_tracked_var("charge_received_grid", 0)
        self.extracted_car_data.init_tracked_var("charge_received_work", 0)
        self.extracted_car_data.init_tracked_var("charge_received_public", 0)
        self.extracted_car_data.init_tracked_var("charge_consumed", 0)
        self.extracted_car_data.init_tracked_var("soc", 0)
        self.extracted_car_data.init_tracked_var("work_charge_instruction", 0)
        self.extracted_car_data.init_tracked_var("home_charge_instruction", 0)
        self.extracted_car_data.init_tracked_var("emergency_charge_instruction", 0)
        self.extracted_car_data.init_tracked_var("charge_held_back", 0)
        self.extracted_car_data.init_tracked_var("electricity_cost_apartment", 0)
        self.extracted_car_data.init_tracked_var("electricity_cost_house_w_pv", 0)
        self.extracted_car_data.init_tracked_var("electricity_cost_house_wo_pv", 0)
        self.extracted_car_data.init_tracked_var("distance_travelled_apartment", 0)
        self.extracted_car_data.init_tracked_var("distance_travelled_house_w_pv", 0)
        self.extracted_car_data.init_tracked_var("distance_travelled_house_wo_pv", 0)
        self.co.t_print("Start to create agents")
        for agent_uid in range (self.num_agents):
            car_tracking_id \
                = self.extracted_car_data.init_tracked_agent(agent_uid)
            residency_location = self.lrm.draw_location_of_residency()
            employment_location = \
                self.lrm.draw_location_of_employment(residency_location)
            # residency_location = self.lrm.locations[21002]
            # employment_location = self.lrm.locations[21402]
            company = self.cpm.add_employee_to_location(employment_location)
            
            cur_activity = self.cp.HOME       # actually assigned once
            cur_location = residency_location # calendars are generated
            pos = self.lrm.relative_location_position(cur_location)
            
            house_agent = HouseAgent(agent_uid, self, self.parameters,
                                     self.clock, residency_location, company,
                                     self.chm, self.epm, self.hcm, self.hgm)
            car_agent = CarAgent(agent_uid, self, car_tracking_id, self.clock,
                                 cur_activity, cur_location, house_agent,
                                 company, self.lrm, self.cmm, self.wm, self.cp,
                                 self.extracted_car_data, self.parameters)
            self.schedule_houses.add(house_agent)
            self.schedule_cars.add(car_agent)
            self.space.place_agent(car_agent, pos)
        
        self.co.t_print("Agent creation complete")
        self.co.t_print("Create agent's work schedule")
        self.co.startProgress("calendar_creation", 0,
                              len(self.schedule_cars.agents))
        self.cp.prepare_schedule_generation()
        car_it = 0
        while car_it < len(self.schedule_cars.agents):
            car_agent = self.schedule_cars.agents[car_it]
            self.co.progress("calendar_creation", car_it)
            success = car_agent.generate_calendar_entries()
            if not success:
                self.co.t_print("Calendar creation reseted!")
                self.cp.prepare_schedule_generation()
                car_it = 0
            car_agent.whereabouts.set_activity_and_location( \
                                    car_agent.calendar.cur_scheduled_activity,
                                    car_agent.calendar.cur_scheduled_location)
            car_it += 1
        self.co.endProgress("calendar_creation",
                            "Completed agent's work schedule")
        self.co.t_print("Agent creation complete")
        self.co.t_print("Current memory usage: {}".format(\
                    get_current_ram_usage()))
        self.co.t_print("INITIALISATION COMPLETE")
        self.co.t_print("")
        self.co.t_print("COMMENCING STEP CALCULATION")
        self.co.startProgress("simulation_step", self.clock.cur_time_step,
                              self.clock.time_step_limit)
        
    def step(self):
        '''Advance the model by one step.'''
        self.co.progress("simulation_step", self.clock.cur_time_step)
        
        if self.clock.cur_time_step == self.parameters.next_stop:
            test = 0
        
        self.clock.step()
        self.hcm.step()
        self.hgm.step()
        self.wm.prepare_movement()
        self.schedule_houses.step()
        self.schedule_cars.step()
        for house_agent in self.schedule_houses.agents:
            house_agent.step_late()
        self.cpm.step()
        
        if self.clock.is_pre_heated:
            for car_agent in self.schedule_cars.agents:
                total_electricity_cost = car_agent.cur_electricity_cost
                if not car_agent.house_agent.is_house:
                    self.extracted_car_data.set(car_agent.tracking_id,
                                                "electricity_cost_apartment",
                                                total_electricity_cost)
                    self.extracted_car_data.set(car_agent.tracking_id,
                                                "distance_travelled_apartment",
                                                car_agent.distance_travelled)
                elif car_agent.house_agent.pv_capacity != 0:
                    self.extracted_car_data.set(car_agent.tracking_id,
                                                "electricity_cost_house_w_pv",
                                                total_electricity_cost)
                    self.extracted_car_data.set(car_agent.tracking_id,
                                                "distance_travelled_house_w_pv",
                                                car_agent.distance_travelled)
                else:
                    self.extracted_car_data.set(car_agent.tracking_id,
                                                "electricity_cost_house_wo_pv",
                                                total_electricity_cost)
                    self.extracted_car_data.set(car_agent.tracking_id,
                                                "distance_travelled_house_wo_pv",
                                                car_agent.distance_travelled)
            
    def summarise_simulation(self):
        self.co.endProgress("simulation_step", "STEP CALCULATION COMPLETE")
        self.co.t_print("")
        self.co.t_print("Summary")
        self.co.t_print("Current memory usage: {}".format(\
                    get_current_ram_usage()))
        
        flat_cars = []
        for car_agent in self.schedule_cars.agents:
            if car_agent.would_run_flat == True:
                flat_cars.append(car_agent.uid)
        if len(flat_cars) == 0:
            self.co.t_print("Cars that would run flat: None")
        else:
            self.co.t_print("Cars that would run flat:" + str(flat_cars))
                
    def total_charge(self):
        total_charge = {"home":0, "work":0, "emergency":0}
        for agent in self.schedule_cars.agents:
            total_charge["home"] += agent.total_charge["home"]
            total_charge["work"] += agent.total_charge["work"]
            total_charge["emergency"] += agent.total_charge["emergency"]
        return total_charge