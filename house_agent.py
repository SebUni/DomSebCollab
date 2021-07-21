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
    def __init__(self, uid, model, clock, residency_location, company,
                 charger_manager, electricity_plan_manager,
                 house_consumption_manager, house_generation_manager,
                 parameters):
        super().__init__(uid, model)
        # uid is redundant because super alreay incorperates unique_id but
        # for brevity and consistency through out the code i define uid
        self.uid = uid
        self.clock = clock
        self.location = residency_location
        
        self.is_house = residency_location.draw_shall_new_dwelling_be_a_house()
        #self.is_house = True
        self.is_house_owned = residency_location.draw_shall_new_house_be_owned()
        #self.is_house_owned = True
        self.occupants = residency_location.draw_occupants_at_random()
        # TODO check how charger is chosen
        # if there is no charger assign "None"
        self.charger = None
        self.battery_capacity = 0
        self.pv_capacity = 0
        if self.is_house:
            charger_model = charger_manager.draw_charger_at_random( \
                                                charger_manager.HOME_CHARGER)        
            self.charger = charger_manager.add_charger(charger_model)
            self.battery_capacity = \
                parameters.get_parameter("battery_capacity","float")
            if self.is_house_owned:
                self.pv_capacity \
                    = residency_location.draw_pv_capacity_on_owned_house_at_random()
                #self.pv_capacity \
                    #= residency_location.pv_avg_capacity
        # TODO check how electricity plan is chosen
        electricity_plan_uid \
            = random.choice(electricity_plan_manager.residential_plan_uids)
        self.electricity_plan \
            = electricity_plan_manager.electricity_plans[electricity_plan_uid]
        self.battery_soc = 0.0
        self.hcm = house_consumption_manager
        self.hgm = house_generation_manager
        self.cur_pv_excess_supply = 0
        self.charging_price_at_company \
            = company.electricity_plan.cost_of_use(1,0);
        self.earnings_from_feed_in = 0
        self.spendings_for_house_consumption = 0
        self.extracted_data = dict()
            
    def charge_car(self, car_agent, charge_up_to):
        """
        Allow the car to charge at the house's charger.

        Parameters
        ----------
        car_agent : CarAgent
            The car_agent attempting to charge
        charge_up_to : float
            The amount of charge the car demands at most.

        Returns
        -------
        delivered_charge : float
            Amount of electricity in kWh provided to the car in this time step.
        charging_cost : float
            Cost in $ incurred for charing delivered_charge.

        """
        delivered_charge = 0.0
        charging_cost = 0.0
        
        max_charge_rate = self.max_charge_rate(car_agent.car_model)
        delivered_charge = min([self.clock.time_step / 60 * max_charge_rate,
                                charge_up_to])
        charging_cost \
             = self.electricity_plan.cost_of_use(delivered_charge,
                                                 self.clock.time_of_day)
        
        return delivered_charge, charging_cost
    
    def max_charge_rate(self, car_model):
        return max(min(car_model.charger_capacity_ac,
                       self.charger.charger_model.power_ac),
                   min(car_model.charger_capacity_dc,
                       self.charger.charger_model.power_dc))
        
    def step(self):
        # 1) Calculate house consumption
        inst_consumption \
            = self.hcm.instantaneous_consumption(self.location, self.occupants)
        cur_consumption = inst_consumption * self.clock.time_step / 60
        # 2) Calculate PV geneation
        inst_generation = self.hgm.instantaneous_generation(self.pv_capacity)
        cur_generation = inst_generation * self.clock.time_step / 60
        self.cur_pv_excess_supply = max(cur_generation - cur_consumption, 0)
        # 3) Determine car charge requirements once car has returned (only
        #    required once time of use is considered)
        
    def step_late(self):
        # 4) Marry house consumption and generation
        feed_in = self.electricity_plan.feed_in_tariff
        charging_price_at_home = self.electricity_plan.cost_of_use(1,
                                                        self.clock.time_of_day)
        if self.cur_pv_excess_supply > 0:
            if self.charging_price_at_company \
                < charging_price_at_home + feed_in:
                self.earnings_from_feed_in += self.cur_pv_excess_supply * feed_in
            else:
                self.battery_soc += self.cur_pv_excess_supply
        else:
            power_to_purchase = - self.cur_pv_excess_supply
            if self.charging_price_at_company \
                < charging_price_at_home + feed_in:
                power_from_battery = min(self.battery_soc, power_to_purchase)
                self.battery_soc -= power_from_battery
                power_to_purchase -= power_from_battery
            self.spendings_for_house_consumption \
                += self.electricity_plan.cost_of_use(power_to_purchase,
                                                     self.clock.time_of_day)