# -*- coding: utf-8 -*-
"""
Created on Thu Feb  4 16:35:38 2021

@author: S3739258
"""

import sys
import random
import math
import numpy
import scipy.stats

from cast import Cast
from csv_helper import CSVHelper

class HouseConsumptionManager():
    """
    Handles the consumption of houses including locational, seasonal and day-
    time dependet differences.
    """
    def __init__(self, clock):
        self.clock = clock
        
        # load hourly consumption data
        cast = Cast("Hourly Consumption")
        self.hourly_consumption = dict()
        csv_helper = CSVHelper("data","hourly_consumption.csv")
        for row in csv_helper.data:
            hour = cast.to_positive_int(row[0], "Hour")
            season_it = self.clock.season*3
            hourly_cons = []
            hourly_cons.append(cast.to_positive_float(row[season_it+1], "10%"))
            hourly_cons.append(cast.to_positive_float(row[season_it+2], "50%"))
            hourly_cons.append(cast.to_positive_float(row[season_it+3], "90%"))
            self.hourly_consumption[hour] = hourly_cons
        
        # load deviation data for consumption
        cast = Cast("Consumption Deviation")
        self.consumption_deviation = dict()
        csv_helper = CSVHelper("data","consumption_deviation.csv")
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
            
        #
        cast = Cast("Consumption Forecast Parameters")
        self.forecast_parameters = dict()
        hourly_forecast_parameters = dict()
        csv_helper = CSVHelper("data","hourly_consumption_fit.csv")
        season_it = self.clock.season * 2 + 1
        for row in csv_helper.data:
            hour = cast.to_positive_int(row[0], "Hour")
            mu = cast.to_positive_float(row[season_it], "mu")
            sig = cast.to_positive_float(row[season_it + 1], "sig")
            hourly_forecast_parameters[hour] = [mu, sig]
            
        for time_step in range(0,24 * 60, self.clock.time_step):
            hour_begin = time_step // 60
            hour_end = (time_step + self.clock.time_step) // 60
            hour_end_remainder = (time_step + self.clock.time_step) % 60
            
            same_hour = hour_begin == hour_end \
                        or (hour_begin == hour_end - 1 \
                            and hour_end_remainder == 0)
            
            if same_hour:
                mu_hour, sig_hour = hourly_forecast_parameters[hour_begin]
                mu_time_step = mu_hour / (self.clock.time_step / 60)
                sig_sqr_time_step = sig_hour ** 2 / (self.clock.time_step / 60)
                
                self.forecast_parameters[time_step] = [mu_time_step,
                                                       sig_sqr_time_step]
            else:
                raise RuntimeError("Demand forecast for 60 % time_step != 0"
                                   + " not implemented")
        
        cur_mu, cur_sig_sqr = 0, 0
        for time in range(0, self.clock.forecast_horizon,self.clock.time_step):
            cur_mu = cur_mu + self.forecast_parameters[time][0]
            cur_sig_sqr = cur_sig_sqr + self.forecast_parameters[time][0]**2
            
        self.forecast_mu, self.forecast_sig = cur_mu, numpy.sqrt(cur_sig_sqr)
        
    def instantaneous_consumption(self, location, occupants):
        hourly_consumption = 0
        
        perc_10 = self.hourly_consumption[self.clock.time_of_day // 60][0]
        perc_50 = self.hourly_consumption[self.clock.time_of_day // 60][1]
        perc_90 = self.hourly_consumption[self.clock.time_of_day // 60][2]
        
        # draw at random between 0 and 1
        rnd = random.random()
        
        # pick right distribution to draw consumption from
        if rnd < 0.1:
            # for 0-10% use linear PDF
            hourly_consumption = perc_10 * math.sqrt(10 * rnd)
        elif rnd < 0.5:
            # for 10-50% use normal distribution fitted using the 10% and 50%
            # CDF marker
            # scipy.stats.norm.ppf is the inverse of the normal CDF
            mu = perc_50
            sig = perc_50 - perc_10
            hourly_consumption = scipy.stats.norm.ppf(rnd, loc=mu, scale=sig)
        else:
            # for 50-100% use normal distribution fitted using the 50% and 90%
            # CDF marker
            # scipy.stats.norm.ppf is the inverse of the normal CDF
            mu = perc_50
            sig = perc_90 - perc_50
            hourly_consumption = scipy.stats.norm.ppf(rnd, loc=mu, scale=sig)
        
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
            prev_forecast_horizon_time_step = cur_time - time_step
            next_forecast_horizon_time_step \
                = ( (cur_time + horizon) // time_step  \
                    -((cur_time + horizon) % time_step == 0) * 1 ) * time_step
                
            pf_prm = self.forecast_parameters[prev_forecast_horizon_time_step]
            nf_prm = self.forecast_parameters[next_forecast_horizon_time_step]
            self.forecast_mu = self.forecast_mu - pf_prm[0] + nf_prm[0]
            self.forecast_sig = numpy.sqrt(self.forecast_sig**2 - pf_prm[1] \
                                           + nf_prm[1])
        
    
    def consumption_forecast_distribution_parameters(self):
        return self.forecast_mu, self.forecast_sig