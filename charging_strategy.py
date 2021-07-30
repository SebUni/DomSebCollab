# -*- coding: utf-8 -*-
"""
Created on Wed Jul 28 15:05:58 2021

@author: S3739258
"""

import math
import numpy as np
from scipy.special import erf, erfinv

"""
PARAMETER EXPLANATION

q_h (q_home) 
    quantity charged at home
q_ow (q_one_way)
    charge needed to reach next destination
q_r (q_real)
    realisation of the house demand-supply-'balance'
q_w (q_work)
    quantity charged at work
p_w (p_work)
    price paid per kWh at work
p_f (p_feed)
    price received for feeding rooftop pv into grid
p_g (p_grid)
    price paid per kWh at home
p_em (p_emergency)
    most expensive price paid on the road to next to charging in case of
    emergency charging
soc
    state of charge of the EV's battery
c
    confidence with which best cases are expected
mu
    mean for predicition of rooftop pv output
sig
    standard deviation for predicition of rooftop pv output
phi
    value at risk
"""

# TODO update in draw.io ClassDiagram

def parm_cost_fct_charging_at_home_anal(q_ow, q_res, p_f, p_g, p_em, p_w, soc,
                                        c, mu, sig):
    q_tw, q_th = q_ow + q_res, q_ow
    sqrt2sig = math.sqrt(2) * sig
    # performance helper
    thresh = mu + sqrt2sig * erfinv(1 - 2*c)
    # shorthands
    dp = p_g - p_f
    dp_div = dp / (2 * (1 - c))
    
    instruction = 0
    if thresh < q_tw - soc:
        if p_g < p_w:
            instruction = q_tw + q_th - soc
        elif p_g == p_w:
            instruction = q_tw - soc
        else:
            instruction = q_tw - soc
    elif q_tw + q_th - soc < thresh:
        if p_w <= p_f + dp_div * (erf((q_tw - soc - mu) / sqrt2sig) + 1):
            instruction = q_tw - soc
        elif p_w >= p_f + dp_div * (erf((q_tw + q_th - soc - mu) / sqrt2sig) + 1):
            instruction = q_tw + q_th - soc
        else:
            instruction = sqrt2sig * erfinv((p_w - p_f) / dp_div - 1) + mu
    else:
        if p_w > p_g:
            instruction = q_tw + q_th - soc
        elif p_w == p_g:
            instruction = q_tw + q_th - soc
        elif p_f + dp_div * (erf((q_tw - soc - mu) / sqrt2sig) + 1) < p_w < p_g:
            instruction = sqrt2sig * erfinv((p_w - p_f) / dp_div - 1) + mu
        else:
            instruction = q_tw - soc
            
    return max(0, instruction)

def parm_cost_fct_charging_at_work_anal(q_ow, q_res, p_f, p_g, p_em, p_w, soc,
                                        c, mu, sig):
    q_tw, q_th = q_ow, q_ow + q_res
    sqrt2sig = math.sqrt(2) * sig
    # performance helper
    thresh = mu + sqrt2sig * erfinv(1 - 2*c)
    # shorthands
    dp = p_g - p_f
    dp_div = dp / (2 * (1 - c))
    
    instruction = 0
    if q_tw < thresh:
        if p_w >= p_f + dp_div * (erf((q_tw - mu) / sqrt2sig) + 1):
            instruction = q_th - soc
        elif p_w <= p_f + dp_div * (1 - erf(mu / sqrt2sig)):
            instruction = q_th + q_tw - soc
        else:
            instruction = q_th + q_tw - soc - mu \
                - sqrt2sig * erfinv((p_w - p_f) / dp_div - 1)
    elif thresh < 0:
        if p_g < p_w:
            instruction = q_th - soc
        elif p_g == p_w:
            instruction = q_th - soc
        else:
            instruction = q_th + q_tw - soc
    else:
        if p_w < p_g:
            instruction = q_th + q_tw - soc
        elif p_w == p_g:
            instruction = q_th - soc
        elif p_f + dp_div * (erf(q_tw - mu) / sqrt2sig + 1) > p_w > p_g:
            instruction = q_th + q_tw - soc - mu \
                - sqrt2sig * erfinv((p_w - p_f) / dp_div - 1)
        else:
            instruction = q_th - soc
            
    return max(0, instruction)

def round_down_time_step(time_in_hours, time_step_in_min):
    time_in_min = int(time_in_hours * 60)
    time_in_min -= time_in_min % time_step_in_min
    return time_in_min / 60

class ChargingStrategy():
    def __init__(self, car_agent):
        self.ALWAYS_CHARGE = 0
        self.ALWAYS_CHARGE_NO_WORK_CHARGERS = 1
        self.ALWAYS_CHARGE_AT_HOME = 2
        self.ALWAYS_CHARGE_AT_WORK = 3
        self.CHARGE_WHERE_CHEAPER_BASIC = 4
        self.CHARGE_WHERE_CHEAPER_ADVANCED = 5
        
        self.ca = car_agent
        self.parameters = car_agent.parameters
        self.clock = car_agent.clock
        self.cp = car_agent.cp
        self.whereabouts = car_agent.whereabouts
        self.house_agent = car_agent.house_agent
        self.company = car_agent.company
        
        travel_time = self.ca.lrm.estimated_travel_time_between_locations(
                            self.house_agent.location, self.company.location)
        commute_time = travel_time + self.ca.calendar.time_reserve
        rounded_commute_time = (commute_time // self.clock.time_step) \
            * self.clock.time_step
        self.commute_duration = rounded_commute_time / 60
        
        self.reserve_charge = max(car_agent.reserve_power,
                                  car_agent.minimum_absolute_state_of_charge)
        self.q_one_way = car_agent.charge_needed_for_route(
                    car_agent.lrm.calc_route(car_agent.house_agent.location,
                                             car_agent.company.location))
        self.c = car_agent.parameters.get_parameter("confidence", "float")
        self.feed_in_tariff = car_agent.house_agent.electricity_plan.feed_in_tariff
        self.cost_home_charging \
            = car_agent.house_agent.electricity_plan.cost_of_use(1, 
                                                car_agent.clock.time_of_day)
        self.cost_work_charging = car_agent.company.charger_cost_per_kWh
        self.cost_public_charging \
            = car_agent.parameters.get_parameter("public_charger_cost_per_kWh",
                                                 "float")
        self.charging_model \
            = car_agent.parameters.get_parameter("charging_model", "int")
            
        self.charge_rate_at_home \
            = car_agent.house_agent.max_charge_rate(car_agent.car_model)
        self.charge_rate_at_work \
            = car_agent.company.ccm.max_charge_rate(car_agent.car_model)
        self.charge_rate_at_public \
            = car_agent.whereabouts.cur_location.companies[0].ccm.max_charge_rate(car_agent.car_model)
        self.minimum_soc = car_agent.car_model.battery_capacity * \
            self.parameters.get_parameter("minimum_relative_state_of_charge",
                                          "float")
    
    def determine_charge_instructions(self, soc):
        charge_at_home = 0
        charge_at_work = 0
        
        p_work = self.cost_work_charging
        p_feed = self.feed_in_tariff
        p_grid = self.cost_home_charging
        p_em = self.cost_public_charging
        
        q_ow = self.q_one_way
        q_res =  self.reserve_charge
        
        c  = self.c
        mu, sig = self.ca.calc_total_forcast_mean_and_std_dev()
        
        pv_cap = self.house_agent.pv_capacity
        
        cr_h = self.charge_rate_at_home
        cr_w = self.charge_rate_at_work
        cr_p = self.charge_rate_at_public
        
        cal = self.ca.calendar
        
        # model #0: basics - charge always to 80%
        if self.charging_model == self.ALWAYS_CHARGE \
            or self.charging_model == self.ALWAYS_CHARGE_NO_WORK_CHARGERS:
            if self.whereabouts.destination_activity == self.cp.WORK:
                charge_at_work \
                    = max(self.ca.car_model.battery_capacity * 0.8 - soc, 0)
            if self.whereabouts.destination_activity == self.cp.HOME:
                if self.house_agent.charger != None:
                    charge_at_home \
                        = max(self.ca.car_model.battery_capacity*0.8 - soc, 0)
                else:
                    charge_needed = max(q_ow + q_res - soc, 0)
                    if charge_needed != 0:
                        self.ca.initiate_emergency_charging(charge_needed)
                    
        # model #1: basics -  no work charging available
        # requires basic model #1 to be active
        if self.charging_model == self.ALWAYS_CHARGE_NO_WORK_CHARGERS:
            charge_at_work = 0
                
        # model #4: basics - charge where cheaper
        if self.charging_model == self.CHARGE_WHERE_CHEAPER_BASIC:
            if self.whereabouts.destination_activity == self.cp.WORK\
                and p_work <= p_grid:
                work_stay_duration \
                    = ((cal.find_next_departure_from_activity(self.cp.WORK)\
                    - self.clock.elapsed_time) / 60) % (24 * 7)
                charge_at_work \
                    = max(min(self.ca.car_model.battery_capacity * 0.8 - soc,
                              work_stay_duration * self.charge_rate_at_work),0)
            if self.whereabouts.destination_activity == self.cp.HOME:
                if self.house_agent.charger != None:
                    if p_work >= p_grid:
                        home_stay_duration \
                            = ((cal.find_next_departure_from_activity(self.cp.HOME)\
                                - self.clock.elapsed_time) / 60) % (24 * 7)
                        charge_at_home \
                            = max(min(home_stay_duration*self.charge_rate_at_home,
                                     self.ca.car_model.battery_capacity*0.8-soc),0)
                else:
                    charge_needed = max(q_ow + q_res - soc, 0)
                    if charge_needed != 0:
                        self.ca.initiate_emergency_charging(charge_needed)
        
        # model #5: advanced - incluing PV
        if self.charging_model == self.CHARGE_WHERE_CHEAPER_ADVANCED:
            if self.whereabouts.destination_activity == self.cp.WORK:
                if pv_cap != 0 and self.house_agent.charger != None:
                    charge_at_work = parm_cost_fct_charging_at_work_anal(q_ow,
                        q_res, p_feed, p_grid, p_em, p_work,soc,c,mu,sig)
                elif pv_cap == 0 and self.house_agent.charger != None:
                    charge_at_work = max(2 * q_ow + q_res - soc, 0) \
                                                if p_grid > p_work \
                                                else max(q_ow + q_res - soc, 0)
                else:
                    charge_at_work = max(2 * q_ow + q_res - soc, 0)
            if self.whereabouts.destination_activity == self.cp.HOME:
                if pv_cap != 0 and self.house_agent.charger != None:
                    charge_at_home = parm_cost_fct_charging_at_home_anal(q_ow,
                        q_res, p_feed, p_grid, p_em, p_work, soc, c, mu, sig)
                elif pv_cap == 0 and self.house_agent.charger != None:
                    charge_at_home = max(2 * q_ow + q_res - soc, 0) \
                                                if p_grid <= p_work \
                                                else max(q_ow + q_res - soc, 0)    
                else:
                    charge_needed = max(q_ow + q_res - soc, 0)
                    if charge_needed != 0:
                        self.ca.initiate_emergency_charging(charge_needed)
                        return 0, 0
                        
        # charge from alternative source
        # that is if usually prefer to charge at work, check if additional
        # charge is needed
        if self.charging_model in [self.ALWAYS_CHARGE_AT_HOME,
                                   self.ALWAYS_CHARGE_AT_WORK,
                                   self.CHARGE_WHERE_CHEAPER_BASIC,
                                   self.CHARGE_WHERE_CHEAPER_ADVANCED]:
            if self.whereabouts.destination_activity == self.cp.WORK \
                and p_grid < p_work:
                # check if agent needs to charge now to reach all future stops
                soc_check = soc
                shifts_to_come = self.det_shifts_to_come()
                shifts_to_come.append(shifts_to_come.pop(0))
                charge_instruction_at_work = 0
                for shift_it, shift in enumerate(shifts_to_come):
                    # is charge needed to get to home? # CONTINUE FROM HERE
                    soc_check -= q_ow
                    charge_needed_to_home \
                        = self.calc_charge_need_to_reach_home(soc_check,
                                                shifts_to_come, shift_it, True)
                    # is charge neeed to get back home?
                    # shift  is the shift following after this home stay
                    next_time_at_home = self.calc_time_at_home(shift)
                    soc_check = min(soc_check + cr_h * next_time_at_home,
                                    self.ca.car_model.battery_capacity)
                    soc_check -= q_ow
                    charge_needed_to_work \
                        = self.calc_charge_need_to_reach_home(soc_check,
                                               shifts_to_come, shift_it, False)
                    # see if charge needed exceeds previously found demand
                    charge_instruction_at_work \
                        = max(charge_instruction_at_work,charge_needed_to_work,
                              charge_needed_to_home)
                charge_at_work = max(charge_at_work,charge_instruction_at_work)
            if self.whereabouts.destination_activity == self.cp.HOME \
                and p_grid > p_work:
                # check if agent needs to charge now to reach all future stops
                soc_check = soc
                shifts_to_come = self.det_shifts_to_come()
                charge_instruction_at_home = 0
                for shift_it, shift in enumerate(shifts_to_come):
                    # is charge needed to get to work?
                    soc_check -= q_ow
                    charge_needed_to_work \
                        = self.calc_charge_need_to_reach_shift(soc_check,
                                                shifts_to_come, shift_it, True)
                    # is charge neeed to get back home?
                    next_shift_length = self.calc_shift_length(shift)
                    soc_check = min(soc_check + cr_w * next_shift_length, 
                                    self.ca.car_model.battery_capacity)
                    soc_check -= q_ow
                    charge_needed_to_home \
                        = self.calc_charge_need_to_reach_shift(soc_check,
                                               shifts_to_come, shift_it, False)
                    # see if charge needed exceeds previously found demand
                    charge_instruction_at_home \
                        = max(charge_instruction_at_home,charge_needed_to_work,
                              charge_needed_to_home)
                charge_at_home = max(charge_at_home,charge_instruction_at_home)
        
        # boost charge by using public chargers if needed
        if charge_at_home != 0:
            home_stay_duration \
                = ((cal.find_next_departure_from_activity(self.cp.HOME)\
                    - self.clock.elapsed_time) / 60) % (24 * 7)
            if cr_h * home_stay_duration < charge_at_home:
                # determine the fraction of time of home_stay_duration that
                # car should actually charge at home, the rest is time spend
                # charging at public charger
                charge_time_home \
                    = (charge_at_home - home_stay_duration*cr_p)/(cr_h - cr_p)
                charge_time_home = round_down_time_step(charge_time_home,
                                                        self.clock.time_step)
                # determine fraction of charge_at_home that can be charged at
                # home the rest is charged at public charger
                charge_frac_home = charge_time_home * cr_h
                max_charge_at_public = cr_p \
                    * max(home_stay_duration - self.clock.time_step / 60, 0)
                public_frac_charge = charge_at_home - charge_frac_home
                public_at_charge = min(max(public_frac_charge, 0),
                                       max_charge_at_public)
                if public_at_charge != 0:
                    self.ca.initiate_emergency_charging(public_at_charge)
                return 0, 0
            
        if charge_at_work != 0:
            work_stay_duration \
                = ((cal.find_next_departure_from_activity(self.cp.WORK)\
                    - self.clock.elapsed_time) / 60) % (24 * 7)
            if cr_w * work_stay_duration < charge_at_work:
                # determine the fraction of time of work_stay_duration that
                # car should actually charge at work, the rest is time spend
                # charging at public charger
                charge_time_work \
                    = (charge_at_work - work_stay_duration*cr_p)/(cr_w - cr_p)
                charge_time_work = round_down_time_step(charge_time_work,
                                                        self.clock.time_step)
                # determine fraction of charge_at_work that can be charged at
                # work the rest is charged at public charger
                charge_frac_work = charge_time_work * cr_w
                max_charge_at_public = cr_p \
                    * max(work_stay_duration - self.clock.time_step / 60, 0)
                public_frac_charge = charge_at_work - charge_frac_work
                public_at_charge = min(max(public_frac_charge, 0),
                                       max_charge_at_public)
                if public_at_charge != 0:
                    self.ca.initiate_emergency_charging(public_at_charge)
                return 0, 0
        
        return charge_at_home, charge_at_work         
    
    def det_shifts_to_come(self):
        shifts_to_come = []
        cur_time_in_hours = round(self.clock.elapsed_time / 60)
        for time in np.arange(cur_time_in_hours, cur_time_in_hours + 7*24, 1):
            for it, start in enumerate(self.ca.calendar.starts):
                if time % (7*24) == start:
                    shifts_to_come.append(it)
                    break
        
        return shifts_to_come

    def calc_shift_length(self, shift): 
        shift_len = self.ca.calendar.ends[shift]-self.ca.calendar.starts[shift]
        return shift_len % (7*24)

    def calc_time_at_home(self, next_shift):
        prev_shift = (next_shift - 1) % len(self.ca.calendar.starts)
        arr_at_home = self.ca.calendar.ends[prev_shift] + self.commute_duration
        dep_from_home=self.ca.calendar.starts[next_shift]-self.commute_duration
        return (dep_from_home - arr_at_home) % (24*7)
    
    def calc_charge_need_to_reach_shift(self, soc_check, shifts_to_come,
                                        shift_it, start_at_work):
        if soc_check < self.minimum_soc:
            charge_missing = - soc_check + self.minimum_soc
            tmp_soc = self.minimum_soc
            shifts_going_back = shifts_to_come[:shift_it+1]
            shifts_going_back.reverse()
            for it_rev, shift_rev in enumerate(shifts_going_back):
                next_shift_length = self.calc_shift_length(shift_rev)
                time_at_home = self.calc_time_at_home(shift_rev)
                if shift_rev != shifts_to_come[0]:
                    if not (it_rev == 0 and start_at_work):
                        tmp_soc += self.q_one_way
                        if tmp_soc > self.ca.car_model.battery_capacity: break
                        tmp_soc -= self.charge_rate_at_work * next_shift_length
                    tmp_soc += self.q_one_way
                    tmp_soc += self.charge_rate_at_home * time_at_home
                    charge_missing -= self.charge_rate_at_home * time_at_home
                    if tmp_soc > self.ca.car_model.battery_capacity: break
                    if charge_missing < 0: break
                else:
                    return charge_missing
        return 0

    def calc_charge_need_to_reach_home(self, soc_check, shifts_to_come,
                                       shift_it, start_at_home):
        if soc_check < self.minimum_soc:
            charge_missing = - soc_check + self.minimum_soc
            tmp_soc = self.minimum_soc
            shifts_going_back = shifts_to_come[:shift_it+1]
            shifts_going_back.reverse()
            for it_rev, shift_rev in enumerate(shifts_going_back):
                prev_shift = (shift_rev - 1) % len(shifts_to_come)
                prev_shift_length = self.calc_shift_length(prev_shift)
                time_at_home = self.calc_time_at_home(shift_rev)
                
                if not (it_rev == 0 and start_at_home):
                    tmp_soc += self.q_one_way
                    if tmp_soc > self.ca.car_model.battery_capacity: break
                    tmp_soc -= self.charge_rate_at_home * time_at_home
                    
                if shift_rev != shifts_to_come[0]:
                    tmp_soc += self.q_one_way
                    tmp_soc += self.charge_rate_at_work * prev_shift_length
                    charge_missing \
                        -= self.charge_rate_at_work * prev_shift_length
                    if tmp_soc > self.ca.car_model.battery_capacity: break
                    if charge_missing < 0: break
                else:
                    tmp_soc += self.q_one_way
                    if tmp_soc > self.ca.car_model.battery_capacity: break
                    return charge_missing
        return 0