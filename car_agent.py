# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 13:06:27 2020

@author: S3739258
"""
from mesa import Agent
from collections import deque

class CarAgent(Agent):
    """An agent which can travel along the map."""
    def __init__(self, uid, model, clock, cur_location, house_agent, company,
                 car_model_manager, whereabouts_manager):
        """
        Parameters
        ----------
        uid : int
            Unique of the car agent.
        model : ChargingModel
            The base charging model defined as base for the simulation.
        clock : Clock
            The Handle to the global clock object.
        house_agent : HouseAgent
            The house_agent assigned to this car_agent.
        company : Company
            The company where this agent is working.
        car_model_manager : CarModelManager
            The object handling all car models created in ChargingModel class
        whereabouts_manager : WhereaboutsManager
            The object handling all whereabouts created in ChargingModel class

        Returns
        -------
        None.
        """
        super().__init__(uid, model)
        # uid is redundant because super alreay incorperates unique_id but
        # for brevity and consistency through out the code i define uid
        self.uid = uid 
        self.clock = clock
        self.house_agent = house_agent
        self.company = company
        # TODO reconsider how car models are chosen
        self.car_model = car_model_manager.draw_car_model_at_random()
        self.whereabouts = whereabouts_manager.track_new_agent(uid,
                                                               cur_location)
         # TODO check if all agents should start with 100% SOC
        self.soc = 100.0
        self.calendar = deque([])
        self.charge_at_home = 0.0
        self.charge_at_work = 0.0
        
        self.electricity_cost = 0 # in $
        
    def step(self):
        # Writing this while I should be celebrating christmas, fuck COVID
        self.plan()
        self.move()
        self.charge()
        
    def plan(self):
        """ This function determines if the agent should start a new journey
        in this time step. """
        cur_loc = self.whereabouts.cur_location
        scheduled_loc = self.calendar.popleft()
        if not self.whereabouts.is_traveling and cur_loc != scheduled_loc:
            self.whereabouts.set_destination(scheduled_loc)
            
        # TODO determine charing instructions here
    
    def move(self):
        """ Initiates the calculation of the agent's movement. """
        self.whereabouts.elapse_one_tick()
        new_position \
            = self.model.wm.whereabouts[self.uid].cur_location_coordinates
        self.model.grid.move_agent(self, new_position)
        
    def charge(self):
        """ Charges the EV. """
        if not self.whereabouts.is_traveling and self.soc < 100.0:
            missing_charge = (1 - self.soc) * self.car_model.battery_capacity
            received_charge = 0.0
            charging_cost = 0.0
            charge_up_to = 0.0
            if self.charge_at_home != 0.0 and \
                self.whereabouts.current_location == self.house_agent.location:
                if self.charge_at_home < missing_charge:
                    charge_up_to = self.charge_at_home
                else:
                    charge_up_to = missing_charge
                received_charge, charging_cost \
                    = self.house_agent.charge_car(charge_up_to,
                                            self.car_model.charger_capacity)
            if self.charge_at_work != 0.0 and \
                self.whereabouts.current_location == self.company.location:
                if self.charge_at_work < missing_charge:
                    charge_up_to = self.charge_at_work
                else:
                    charge_up_to = missing_charge
                received_charge, charging_cost \
                    = self.company.charge_car(self, charge_up_to,
                                            self.car_model.charger_capacity)
            
            self.soc += received_charge / self.car_model.battery_capacity
            self.electricity_cost += charging_cost