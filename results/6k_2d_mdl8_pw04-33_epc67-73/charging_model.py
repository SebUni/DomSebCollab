# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 17:46:52 2020

@author: S3739258
"""

import random
import gc

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace

from memory_tracker import MemoryTracker
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

class ChargingModel(Model):
    """The charging model with N agents."""
    def __init__(self, nbr_of_agents, console_output, parameters):
        self.memory_tracker = MemoryTracker()
        self.memory_tracker.track_now("base")
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
        self.extracted_company_data.init_tracked_var("Total revenue", 0)
        self.extracted_company_data.init_tracked_var("Revenue per charger", 0)
        self.cpm = CompanyManager(self.parameters, self.clock, self.chm,
                                  self.epm, self.extracted_company_data)
        self.extracted_location_data = ExtractedData(self.clock)
        self.extracted_location_data.init_tracked_var("Feed in quantity", 0)
        self.extracted_location_data.init_tracked_var("Charged quantity", 0)
        self.lrm = LocationRoadManager(self.parameters, self.cpm, self.clock,
                                       self.extracted_location_data)
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
        
        self.memory_tracker.track_now("read files")
        
        # create agents
        self.co.t_print("Start to create agents")
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
        assign_order = self.det_assign_order()
        assign_order = self.mild_shuffle(assign_order)
        while car_it < len(self.schedule_cars.agents):
            car_agent = self.schedule_cars.agents[assign_order[car_it]]
            self.co.progress("calendar_creation", car_it)
            success = car_agent.generate_calendar_entries()
            if success:
                car_agent.whereabouts.set_activity_and_location( \
                                    car_agent.calendar.cur_scheduled_activity,
                                    car_agent.calendar.cur_scheduled_location)
                car_it += 1
            else:
                self.co.t_print("Calendar creation reseted!")
                self.cp.prepare_schedule_generation()
                assign_order = self.mild_shuffle(assign_order)
                car_it = 0
                
        self.co.endProgress("calendar_creation",
                            "Completed agent's work schedule")
        self.co.t_print("Agent creation complete")
        self.memory_tracker.track_now("created agents")
        self.co.t_print("INITIALISATION COMPLETE")
        self.co.t_print("")
        self.co.t_print("COMMENCING STEP CALCULATION")
        self.co.startProgress("simulation_step", self.clock.cur_time_step,
                              self.clock.time_step_limit)
    
    def det_assign_order(self):
        min_hours = min([agent.calendar.hours_worked_per_week \
                         for agent in self.schedule_cars.agents])
        max_hours = max([agent.calendar.hours_worked_per_week \
                         for agent in self.schedule_cars.agents])
        ass_order = [[agent.uid for agent in self.schedule_cars.agents \
                      if agent.calendar.hours_worked_per_week == i] \
                     for i in range(min_hours,max_hours+1)]
        ass_order.reverse()
        assign_order = [uid for hour_slot in ass_order for uid in hour_slot]
        
        return assign_order
    
    def mild_shuffle(self, lst):
        max_rel_dist = .1
        max_abs_dist = int(len(lst) * max_rel_dist)
        for it in range(len(lst)):
            move_by = random.randint(-max_abs_dist, max_abs_dist)
            if not 0 <= it + move_by < len(lst):
                move_by *= -1
            cur_value = lst[it]
            lst[it] = lst[it+move_by]
            lst[it+move_by] = cur_value
        
        return lst
    
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
        self.lrm.step()
        
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
        self.memory_tracker.track_now("ran steps")
        msg = "Memory useage | Base: {} Agents: {} Steps: {} Total: {}".format(\
            self.memory_tracker.difference("base", "read files"),
            self.memory_tracker.difference("read files", "created agents"),
            self.memory_tracker.difference("created agents", "ran steps"),
            self.memory_tracker.absolute("ran steps"))
        self.co.t_print(msg)
        del msg
        
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
    
    def clear(self):
        for agent in self.schedule_houses.agents:
            self.schedule_houses.remove(agent)
        for agent in self.schedule_cars.agents:
            self.space.remove_agent(agent)
            self.schedule_cars.remove(agent)
        attrs = ["memory_tracker", "clock", "chm", "epm",
                 "extracted_company_data", "cpm", "extracted_location_data",
                 "lrm", "cmm", "cp", "wm", "hcm", "hgm", "schedule_cars",
                 "schedule_houses", "space", "extracted_car_data"]
        for attr in attrs:
            if hasattr(self, attr):
                if hasattr(getattr(self, attr), "clear"):
                    getattr(self, attr).clear()
                delattr(self, attr)
        gc.collect()