# -*- coding: utf-8 -*-
"""
Created on Thu Feb  4 16:35:38 2021

@author: S3739258
"""

import math
import numpy.random

from cast import Cast
from csv_helper import CSVHelper

class HouseConsumptionManager():
    """
    Handles the consumption of houses including locational, seasonal and day-
    time dependet differences.
    """
    def __init__(self, clock, parameters):
        self.clock = clock
        self.parameters = parameters
        
        # load hourly consumption data
        cast = Cast("Hourly Consumption")
        self.hourly_consumption = dict()
        csv_helper = CSVHelper("data","hourly_consumption.csv")
        for row in csv_helper.data:
            day = cast.to_positive_int(row[0], "Day")
            hour = cast.to_positive_int(row[1], "Hour")
            hour_this_week = (day-1)*24+hour
            season_it = self.clock.season*2
            mu = cast.to_positive_float(row[season_it+2], "Hourly Mean")
            sig = cast.to_positive_float(row[season_it+3], "Hourly StdDev")
            self.hourly_consumption[hour_this_week] = [mu, sig]
        
        # load deviation data for consumption
        cast = Cast("Consumption Deviation")
        sa_level = self.parameters.get_parameter("sa_level","int")
        self.consumption_deviation = dict()
        csv_helper = CSVHelper("data/SA" + str(sa_level),
                               "consumption_deviation.csv")
        for row in csv_helper.data:
            location_uid = cast.to_positive_int(row[0], "LocationUid")
            season_it = self.clock.season * 5
            cons_deviation = dict()
            cons_deviation[1] = cast.to_positive_float(row[season_it+1], "1PHH")
            cons_deviation[2] = cast.to_positive_float(row[season_it+2], "2PHH")
            cons_deviation[3] = cast.to_positive_float(row[season_it+3], "3PHH")
            cons_deviation[4] = cast.to_positive_float(row[season_it+4], "4PHH")
            cons_deviation[5] = cast.to_positive_float(row[season_it+5], "5PHH")
            self.consumption_deviation[location_uid] = cons_deviation
            
        
        self.forecast_parameters = dict()
        for time_step in range(0,24 * 60 * 7, self.clock.time_step):
            hour_begin = time_step // 60
            hour_end = (time_step + self.clock.time_step) // 60
            hour_end_remainder = (time_step + self.clock.time_step) % 60
            
            same_hour = hour_begin == hour_end \
                        or (hour_begin == hour_end - 1 \
                            and hour_end_remainder == 0)
            
            if same_hour:
                mu_hour, sig_hour = self.hourly_consumption[hour_begin]
                mu_time_step = mu_hour / (self.clock.time_step / 60)
                sig_sqr_time_step = sig_hour ** 2 / (self.clock.time_step / 60)
                
                self.forecast_parameters[time_step] = [mu_time_step,
                                                       sig_sqr_time_step]
            else:
                raise RuntimeError("Demand forecast for 60 % time_step != 0"
                                   + " not implemented")
        
        cur_mu, cur_sig_sqr = 0, 0
        for time_it in range(0, self.clock.forecast_horizon,self.clock.time_step):
            time = time_it % (24 * 60 * 7)
            cur_mu += self.forecast_parameters[time][0]
            cur_sig_sqr += self.forecast_parameters[time][0]**2
            
        self.forecast_mu, self.forecast_sig = cur_mu, math.sqrt(cur_sig_sqr)
        
    def instantaneous_consumption(self, location, occupants):
        
        mu = self.hourly_consumption[self.clock.time_of_week // 60][0]
        sig = self.hourly_consumption[self.clock.time_of_week // 60][1]
        
        hourly_consumption = -1.0
        while hourly_consumption < 0.0:
            hourly_consumption = numpy.random.normal(mu, sig)
        
        # adapt consumption for location and occupants
        occupants_it = min(occupants, 5)
        deviation = self.consumption_deviation[location.uid][occupants_it]
        
        inst_consumption = hourly_consumption * deviation
            
        return inst_consumption
    
    def step(self):
        if self.clock.elapsed_time != 0:
            cur_time = self.clock.elapsed_time
            horizon = self.clock.forecast_horizon
            time_step = self.clock.time_step
            prev_forecast_horizon_time_step \
                = (cur_time - time_step) % (7 * 24 * 60)
            next_forecast_horizon_time_step \
                = ( (cur_time + horizon) // time_step  \
                    -((cur_time + horizon) % time_step == 0) * 1 ) \
                  * time_step % (7 * 24 * 60)
                
            pf_prm = self.forecast_parameters[prev_forecast_horizon_time_step]
            nf_prm = self.forecast_parameters[next_forecast_horizon_time_step]
            self.forecast_mu += - pf_prm[0] + nf_prm[0]
            self.forecast_sig = math.sqrt(self.forecast_sig**2 - pf_prm[1] \
                                           + nf_prm[1])
        
    def consumption_forecast_distribution_parameters(self):
        return self.forecast_mu, self.forecast_sig