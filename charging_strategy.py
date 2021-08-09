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
    def __init__(self, parameters, car_agent=None):
        self.ALWAYS_CHARGE = 0
        self.ALWAYS_CHARGE_NO_WORK_CHARGERS = 1
        self.ALWAYS_CHARGE_AT_HOME = 2
        self.ALWAYS_CHARGE_AT_WORK = 3
        self.ALWAYS_CHARGE_WHERE_CHEAPER = 4
        self.CHARGE_WHERE_CHEAPER_BASIC = 5
        self.CHARGE_WHERE_CHEAPER_ADVANCED = 6
        self.charging_model = parameters.get("charging_model", "int")
        self.charging_model_names = {0: "Always charge",
                                     1: "Always charge (no work chargers)",
                                     2: "Always charge at home",
                                     3: "Always charge at work",
                                     4: "Always_charge where cheaper",
                                     5: "Charge where cheaper basic",
                                     6: "Charge where cheaper advanced"}
        if car_agent == None: return
        
        
        self.ca = car_agent
        self.parameters = parameters
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
                    car_agent.lrm.calc_route(self.house_agent.location,
                                             car_agent.company.location))
        self.c = parameters.get("confidence", "float")
        self.feed_in_tariff = self.house_agent.electricity_plan.feed_in_tariff
        self.cost_home_charging \
            = self.house_agent.electricity_plan.cost_of_use(1, 
                                                car_agent.clock.time_of_day)
        self.cost_work_charging = car_agent.company.charger_cost_per_kWh
        self.cost_public_charging \
            = parameters.get("public_charger_cost_per_kWh", "float")            
        self.charge_rate_at_home \
            = self.house_agent.max_charge_rate(car_agent.car_model)
        self.charge_rate_at_work \
            = car_agent.company.ccm.max_charge_rate(car_agent.car_model)
        self.charge_rate_at_public \
            = car_agent.whereabouts.cur_location.companies[0].ccm.max_charge_rate(car_agent.car_model)
        self.minimum_soc = max(car_agent.car_model.battery_capacity * \
            self.parameters.get("minimum_relative_state_of_charge", "float"),
                               self.reserve_charge)
        self.always_charge_from_pv \
            = True if self.cost_work_charging > self.feed_in_tariff else False
        if self.charging_model not in [self.CHARGE_WHERE_CHEAPER_BASIC,
                                       self.CHARGE_WHERE_CHEAPER_ADVANCED] \
            or not self.house_agent.is_house:
            self.always_charge_from_pv = False
    
    def determine_charge_instructions(self, soc):
        if not hasattr(self,'ca'):
            raise RuntimeError("charging_strategy: Initialised without car_agent")
        charge_at_home = 0
        charge_at_work = 0
        
        p_work = self.cost_work_charging
        p_feed = self.feed_in_tariff
        p_grid = self.cost_home_charging
        p_em = self.cost_public_charging
        
        q_ow = self.q_one_way
        q_res =  self.reserve_charge
        
        c  = self.c
        
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
                
        # model #4: basics - always charge where cheaper
        if self.charging_model == self.ALWAYS_CHARGE_WHERE_CHEAPER:
            if self.whereabouts.destination_activity == self.cp.WORK\
                and p_work <= p_grid:
                work_stay_duration \
                    = ((cal.find_next_departure_from_activity(self.cp.WORK)\
                    - self.clock.elapsed_time) / 60) % (24 * 7)
                charge_at_work \
                    = max(min(self.ca.car_model.battery_capacity * 0.8 - soc,
                              work_stay_duration * cr_w),0)
            if self.whereabouts.destination_activity == self.cp.HOME:
                if self.house_agent.charger != None:
                    if p_work >= p_grid:
                        home_stay_duration \
                            = ((cal.find_next_departure_from_activity(self.cp.HOME)\
                                - self.clock.elapsed_time) / 60) % (24 * 7)
                        charge_at_home \
                            = max(min(self.ca.car_model.battery_capacity*0.8-soc,
                                      home_stay_duration * cr_h),0)
                else:
                    charge_needed = max(q_ow + q_res - soc, 0)
                    if charge_needed != 0:
                        self.ca.initiate_emergency_charging(charge_needed)
                        
        # model #5: basics - charge where cheaper
        if self.charging_model == self.CHARGE_WHERE_CHEAPER_BASIC:
            if self.whereabouts.destination_activity == self.cp.WORK:
                work_stay_duration \
                    = ((cal.find_next_departure_from_activity(self.cp.WORK)\
                    - self.clock.elapsed_time) / 60) % (24 * 7)
                if p_grid > p_work:
                    charge_at_work = q_ow
                if p_grid >= p_work:
                    charge_at_work += q_ow + q_res - soc
                charge_at_work = max(min(work_stay_duration * cr_w,
                                         charge_at_work),0)
            if self.whereabouts.destination_activity == self.cp.HOME:
                if self.house_agent.charger != None:
                    home_stay_duration \
                        = ((cal.find_next_departure_from_activity(self.cp.HOME)\
                            - self.clock.elapsed_time) / 60) % (24 * 7)
                    if p_grid < p_work:
                        charge_at_home = q_ow
                    if p_grid <= p_work:
                        charge_at_home += q_ow + q_res - soc
                    charge_at_home = max(min(home_stay_duration * cr_h,
                                             charge_at_home),0)
                else:
                    charge_needed = max(q_ow + q_res - soc, 0)
                    if charge_needed != 0:
                        self.ca.initiate_emergency_charging(charge_needed)
        
        # model #6: advanced - incluing PV
        if self.charging_model == self.CHARGE_WHERE_CHEAPER_ADVANCED:
            next_home_stay_start, next_home_stay_end \
                = self.det_next_home_stay()
            forcast_begin = max(self.clock.elapsed_time, next_home_stay_start)
            mu, sig \
                = self.ca.calc_forcast_mean_and_std_dev(forcast_begin,
                                                        next_home_stay_end)
            if self.whereabouts.destination_activity == self.cp.WORK:
                # when agents earn more by selling PV than using it to charge
                if p_feed >= p_work:
                    charge_at_work = 2 * q_ow + q_res - soc
                # when charging from grid is more expensive than at work but
                # charging from PV is better than selling PV at feed in cost
                elif p_grid >= p_work:
                    # car can charge at home also from PV and forecast is not 0
                    if pv_cap != 0 and self.house_agent.charger != None \
                        and sig > 0:
                        charge_at_work \
                            = parm_cost_fct_charging_at_work_anal(q_ow, q_res,
                                p_feed, p_grid, p_em, p_work,soc,c,mu,sig)
                    # car can charge at home but NOT from PV or car can NOT\
                    # charge at home
                    else:
                        charge_at_work = 2 * q_ow + q_res - soc
                # when only public charging is more expen. than work charging
                else:
                    charge_at_work = q_ow + q_res - soc
                # ensure charge suffices to reach home, but uses as little 
                # public charging as possible
                work_stay_duration \
                    = ((cal.find_next_departure_from_activity(self.cp.WORK)\
                    - self.clock.elapsed_time) / 60) % (24 * 7)
                charge_at_work = max(charge_at_work, 0)
            if self.whereabouts.destination_activity == self.cp.HOME:
                if self.house_agent.charger != None:
                    home_stay_duration \
                        = ((cal.find_next_departure_from_activity(self.cp.HOME)\
                            - self.clock.elapsed_time) / 60) % (24 * 7)
                    charge_at_home = q_ow + q_res - soc
                    if p_grid < p_work:
                        charge_at_home += q_ow
                    charge_at_home = max(charge_at_home, 0)
                else:
                    charge_needed = max(q_ow + q_res - soc, 0)
                    if charge_needed != 0:
                        self.ca.initiate_emergency_charging(charge_needed)
        
        # boost charge by using public chargers if needed to reach next
        # destination
        if charge_at_home != 0:
            charge_needed_to_work = max(q_ow + q_res - soc, 0)
            home_stay_duration \
                = ((cal.find_next_departure_from_activity(self.cp.HOME)\
                    - self.clock.elapsed_time) / 60) % (24 * 7)
            if cr_h * home_stay_duration <= charge_needed_to_work:
                # determine the fraction of time of home_stay_duration that
                # car should actually charge at home, the rest is time spend
                # charging at public charger
                charge_time_home \
                    = (charge_needed_to_work - home_stay_duration * cr_p) \
                    / (cr_h - cr_p)
                charge_time_home = round_down_time_step(charge_time_home,
                                                        self.clock.time_step)
                # determine fraction of charge_at_home that can be charged at
                # home the rest is charged at public charger
                charge_frac_home = charge_time_home * cr_h
                # public charge limited by charge time and charge rate
                max_charge_at_public_cr = cr_p \
                    * max(home_stay_duration - self.clock.time_step / 60, 0)
                # public charge limited by battery capacity
                max_charge_at_public_bat \
                    = self.ca.car_model.battery_capacity - soc
                max_charge_at_public = min(max_charge_at_public_cr,
                                           max_charge_at_public_bat)
                public_frac_charge = charge_needed_to_work - charge_frac_home
                public_at_charge = max(min(public_frac_charge,
                                       max_charge_at_public), 0)
                if public_at_charge != 0:
                    self.ca.initiate_emergency_charging(public_at_charge)
                return 0, 0
            
        if charge_at_work != 0:
            charge_needed_to_home = max(q_ow + q_res - soc, 0)
            work_stay_duration \
                = ((cal.find_next_departure_from_activity(self.cp.WORK)\
                    - self.clock.elapsed_time) / 60) % (24 * 7)
            if cr_w * work_stay_duration <= charge_needed_to_home:
                # determine the fraction of time of work_stay_duration that
                # car should actually charge at work, the rest is time spend
                # charging at public charger
                charge_time_work \
                    = (charge_needed_to_home - work_stay_duration * cr_p)\
                    / (cr_w - cr_p)
                charge_time_work = round_down_time_step(charge_time_work,
                                                        self.clock.time_step)
                # determine fraction of charge_at_work that can be charged at
                # work the rest is charged at public charger
                charge_frac_work = charge_time_work * cr_w
                # public charge limited by charge time and charge rate
                max_charge_at_public_cr = cr_p \
                    * max(work_stay_duration - self.clock.time_step / 60, 0)
                # public charge limited by battery capacity
                max_charge_at_public_bat \
                    = self.ca.car_model.battery_capacity - soc
                max_charge_at_public = min(max_charge_at_public_cr,
                                           max_charge_at_public_bat)
                public_frac_charge = charge_needed_to_home - charge_frac_work
                public_at_charge = max(min(public_frac_charge,
                                       max_charge_at_public), 0)
                if public_at_charge != 0:
                    self.ca.initiate_emergency_charging(public_at_charge)
                return 0, 0
                        
        # increase primary charge (the source that is cheaper) if necessary
        if self.charging_model in [self.CHARGE_WHERE_CHEAPER_BASIC,
                                   self.CHARGE_WHERE_CHEAPER_ADVANCED]:
            if self.whereabouts.destination_activity == self.cp.WORK \
                and p_grid >= p_work:
                # check if agent needs to charge now to reach all future stops
                soc_check = soc
                shifts_to_come = self.det_shifts_to_come()
                charge_instruction_at_work = 0
                for shift_it, shift in enumerate(shifts_to_come):
                    # add charge agent can charge now
                    # TODO to be precise this would need to check if the first
                    # shift is shorter due to a delayed arrival
                    next_shift_length = self.calc_shift_length(shift)
                    soc_check = min(max(2 * q_ow + q_res, soc_check),
                                    soc_check + cr_w * next_shift_length,
                                    self.ca.car_model.battery_capacity)
                    # is charge needed to get to home?
                    soc_check -= q_ow
                    charge_needed_to_home \
                        = self.calc_charge_need_from_pri_source_to_reach_shift(\
                            soc, soc_check, shifts_to_come, shift_it, False)
                    # is charge neeed to get back home?
                    soc_check -= q_ow
                    charge_needed_to_work \
                        = self.calc_charge_need_from_pri_source_to_reach_shift(\
                            soc, soc_check, shifts_to_come, shift_it, True)
                    # see if charge needed exceeds previously found demand
                    charge_instruction_at_work \
                        = max(charge_instruction_at_work,charge_needed_to_work,
                              charge_needed_to_home)
                charge_at_work = max(charge_at_work,charge_instruction_at_work)
            if self.whereabouts.destination_activity == self.cp.HOME \
                and p_grid <= p_work and self.house_agent.is_house:
                # check if agent needs to charge now to reach all future stops
                soc_check = soc
                shifts_to_come = self.det_shifts_to_come()
                charge_instruction_at_home = 0
                for shift_it, shift in enumerate(shifts_to_come):
                    # add charge agent can charge now
                    # shift  is the shift following after this home stay
                    next_time_at_home = self.calc_time_at_home(shift)
                    soc_check = min(max(2 * q_ow + q_res, soc_check),
                                    soc_check + cr_h * next_time_at_home,
                                    self.ca.car_model.battery_capacity)
                    # is charge needed to get to work?
                    soc_check -= q_ow
                    charge_needed_to_work \
                        = self.calc_charge_need_from_pri_source_to_reach_home(\
                            soc, soc_check, shifts_to_come, shift_it, False)
                    # is charge neeed to get back home?
                    soc_check -= q_ow
                    charge_needed_to_home \
                        = self.calc_charge_need_from_pri_source_to_reach_home(\
                            soc, soc_check, shifts_to_come, shift_it, True)
                    # see if charge needed exceeds previously found demand
                    charge_instruction_at_home \
                        = max(charge_instruction_at_home,charge_needed_to_work,
                              charge_needed_to_home)
                charge_at_home = max(charge_at_home,charge_instruction_at_home)
            
        
        # charge from alternative source (the more expenise charging option)
        # that is if usually prefer to charge at work, check if additional
        # charge is needed
        if self.charging_model in [self.ALWAYS_CHARGE_AT_HOME,
                                   self.ALWAYS_CHARGE_AT_WORK,
                                   self.ALWAYS_CHARGE_WHERE_CHEAPER,
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
                    # is charge needed to get to home?
                    soc_check -= q_ow
                    charge_needed_to_home \
                        = self.calc_charge_need_from_alt_source_to_reach_home(\
                                    soc_check, shifts_to_come, shift_it, True)
                    # is charge neeed to get back home?
                    # shift  is the shift following after this home stay
                    next_time_at_home = self.calc_time_at_home(shift)
                    soc_check = min(soc_check + cr_h * next_time_at_home,
                                    self.ca.car_model.battery_capacity)
                    soc_check -= q_ow
                    charge_needed_to_work \
                        = self.calc_charge_need_from_alt_source_to_reach_home(\
                                    soc_check, shifts_to_come, shift_it, False)
                    # see if charge needed exceeds previously found demand
                    charge_instruction_at_work \
                        = max(charge_instruction_at_work,charge_needed_to_work,
                              charge_needed_to_home)
                charge_at_work = max(charge_at_work,charge_instruction_at_work)
            if self.whereabouts.destination_activity == self.cp.HOME \
                and p_grid > p_work and self.house_agent.is_house:
                # check if agent needs to charge now to reach all future stops
                soc_check = soc
                shifts_to_come = self.det_shifts_to_come()
                charge_instruction_at_home = 0
                for shift_it, shift in enumerate(shifts_to_come):
                    # is charge needed to get to work?
                    soc_check -= q_ow
                    charge_needed_to_work \
                        = self.calc_charge_need_from_alt_source_to_reach_shift(\
                                    soc_check, shifts_to_come, shift_it, True)
                    # is charge neeed to get back home?
                    next_shift_length = self.calc_shift_length(shift)
                    soc_check = min(soc_check + cr_w * next_shift_length, 
                                    self.ca.car_model.battery_capacity)
                    soc_check -= q_ow
                    charge_needed_to_home \
                        = self.calc_charge_need_from_alt_source_to_reach_shift(\
                                    soc_check, shifts_to_come, shift_it, False)
                    # see if charge needed exceeds previously found demand
                    charge_instruction_at_home \
                        = max(charge_instruction_at_home,charge_needed_to_work,
                              charge_needed_to_home)
                charge_at_home = max(charge_at_home,charge_instruction_at_home)
        
        return charge_at_home, charge_at_work         
    
    def det_shifts_to_come(self):
        shifts_to_come = []
        cur_time_in_hours = round(self.clock.elapsed_time / 60)
        for time in np.arange(cur_time_in_hours, cur_time_in_hours + 7*24, 1):
            for it, start in enumerate(self.ca.calendar.starts):
                if time % (7*24) == start % (7*24):
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
    
    def det_next_home_stay(self):
        # determine shift after next home stay
        time_step = self.clock.time_step
        min_dist = 168
        min_dist_it = 0
        for start_it, start in enumerate(self.ca.calendar.starts):
            dist = (start - self.commute_duration \
                    - self.clock.time_of_week / 60) % (7 * 24)
            if dist < min_dist and dist != 0:
                min_dist = dist
                min_dist_it = start_it
        end_home_stay = (self.ca.calendar.starts[min_dist_it] \
            - self.commute_duration) % (7 * 24)
        end_in_min = end_home_stay * 60
        # adjust for passed time
        offset = (self.clock.elapsed_time // (7 * 24 * 60)) * (7 * 24 * 60)
        end_in_min += offset
        if end_in_min < self.clock.elapsed_time:
            end_in_min += 7 * 24 * 60
        # round to previous 5 min step
        end_in_min_rounded = (end_in_min // time_step) * time_step
        if end_in_min % time_step == 0:
            end_in_min_rounded -= time_step
            
        start_home_stay_in_min \
            = end_in_min - self.calc_time_at_home(min_dist_it) * 60
        # round to next 5 min step
        start_in_min_rounded = (start_home_stay_in_min // time_step)*time_step
        if start_home_stay_in_min % time_step != 0:
            start_in_min_rounded += time_step
            
        return start_in_min_rounded, end_in_min_rounded
    
    def calc_charge_need_from_pri_source_to_reach_shift(self,cur_soc,soc_check,
        shifts_to_come, shift_it, start_at_work):
        if soc_check < self.minimum_soc:
            tmp_soc = self.minimum_soc
            shifts_going_back = shifts_to_come[:shift_it+1]
            shifts_going_back.reverse()
            for it_rev, shift_rev in enumerate(shifts_going_back):
                next_shift_length = self.calc_shift_length(shift_rev)
                time_at_home = self.calc_time_at_home(shift_rev)
                
                if not (it_rev == 0 and start_at_work):
                    tmp_soc += self.q_one_way
                    if tmp_soc > self.ca.car_model.battery_capacity:
                        tmp_soc = self.ca.car_model.battery_capacity
                        
                tmp_soc += self.q_one_way
                if tmp_soc > self.ca.car_model.battery_capacity:
                    tmp_soc = self.ca.car_model.battery_capacity
                if shift_rev != shifts_to_come[0]:
                    tmp_soc -= self.charge_rate_at_work * next_shift_length
                    if tmp_soc < self.minimum_soc: break
                else:
                    return max(tmp_soc - cur_soc, 0)
        return 0

    def calc_charge_need_from_pri_source_to_reach_home(self, cur_soc,soc_check,
        shifts_to_come, shift_it, start_at_home):
        if soc_check < self.minimum_soc:
            tmp_soc = self.minimum_soc
            shifts_going_back = shifts_to_come[:shift_it+1]
            shifts_going_back.reverse()
            for it_rev, shift_rev in enumerate(shifts_going_back):
                time_at_home = self.calc_time_at_home(shift_rev)
                
                if not (it_rev == 0 and not start_at_home):
                    tmp_soc += self.q_one_way
                    if tmp_soc > self.ca.car_model.battery_capacity:
                        tmp_soc = self.ca.car_model.battery_capacity
                    
                tmp_soc += self.q_one_way
                if tmp_soc > self.ca.car_model.battery_capacity: 
                    tmp_soc = self.ca.car_model.battery_capacity
                if shift_rev != shifts_to_come[0]:
                    tmp_soc -= self.charge_rate_at_home * time_at_home
                    if tmp_soc < self.minimum_soc: break
                else:
                    return max(tmp_soc - cur_soc, 0)
        return 0
    
    def calc_charge_need_from_alt_source_to_reach_shift(self, soc_check,
        shifts_to_come, shift_it, start_at_work):
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

    def calc_charge_need_from_alt_source_to_reach_home(self, soc_check,
        shifts_to_come, shift_it, start_at_home):
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