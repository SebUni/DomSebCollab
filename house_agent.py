# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 13:46:56 2020

@author: S3739258
"""

import random

from mesa import Agent

class HouseAgent(Agent):
    """
    An agent which represents the house assgined to a car agent.
    """
    def __init__(self, uid, model, clock, residency_location,
                 charger_manager, electricity_plan_manager):
        super().__init__(uid, model)
        # uid is redundant because super alreay incorperates unique_id but
        # for brevity and consistency through out the code i define uid
        self.uid = uid
        self.clock = clock
        self.location = residency_location
        
        # TODO check how occupants are chosen
        self.occupants = residency_location.draw_occupants_at_random()
        # TODO check how charger is chosen
        # if there is no charger assign "None"
        charger_model_uid \
            = random.choice(charger_manager.residential_model_uids)
        charger_model = charger_manager.charger_models[charger_model_uid]
        self.charger = charger_manager.add_charger(charger_model)
        # TODO check how PV capacity is chosen
        self.pv_capacity = residency_location.draw_pv_capacity_at_random()
        # TODO check how battery capacity is chosen
        self.battery_capacity \
            = residency_location.draw_battery_capacity_at_random()
        # TODO check how electricity plan is chosen
        electricity_plan_uid \
            = random.choice(electricity_plan_manager.residential_plan_uids)
        self.electricity_plan \
            = electricity_plan_manager.electricity_plans[electricity_plan_uid]
        self.battery_soc = 0.0
            
    def charge_car(self, charge_up_to, car_charger_capacity):
        """
        Allow the car to charge at the house's charger.

        Parameters
        ----------
        charge_up_to : float
            The amount of charge the car demands at most.
        car_charger_capacity : float
            Maximum charging rate of the car.

        Returns
        -------
        delivered_charge : float
            Amount of electricity in kWh provided to the car in this time step.
        charging_cost : float
            Cost in $ incurred for charing delivered_charge.

        """
        delivered_charge = 0.0
        charging_cost = 0.0
        
        charge_rate = 0
        if car_charger_capacity < self.charger.power:
            charge_rate = car_charger_capacity
        else:
            charge_rate = self.charger.power
        
        delivered_charge = min([self.clock.time_step / 60 * charge_rate,
                                charge_up_to])
        charging_cost \
            = self.electricity_plan.cost_of_use(delivered_charge,
                                                self.clock.time_of_day)
        
        return delivered_charge, charging_cost