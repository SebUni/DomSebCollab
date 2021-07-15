# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 15:36:10 2021

@author: S3739258
"""

import random
import math

from cast import Cast
from csv_helper import CSVHelper

class HouseGenerationManager():
    def __init__(self, parameters, clock, electricity_plan_manager,
                 car_model_manager):
        self.parameters = parameters
        self.clock = clock
        self.epm = electricity_plan_manager
                
        cast = Cast("Solar Irradation")
        self.irradiances = []
        file_name = "solar_irradiance_" \
                    + self.clock.season_names[self.clock.season] + ".csv"
        csv_helper = CSVHelper("data",file_name)
        it = 0
        resolution_irradiance = 0
        for row in csv_helper.data:
            if it == 0:
                resolution_irradiance \
                    = - cast.to_positive_int(row[0], "Elapsed time")
            if it == 1:
                resolution_irradiance += \
                    + cast.to_positive_int(row[0], "Elapsed time")
            tmp_irradiances = []
            for col in row[1:]:
                value = cast.to_positive_float(col, "Solar irradiance")
                tmp_irradiances.append(value)
            self.irradiances.append(tmp_irradiances)
            it += 1
        
        cast = Cast("Temperatures")
        self.temperatures = []
        file_name = "temperatures_" \
                    + self.clock.season_names[self.clock.season] + ".csv"
        csv_helper = CSVHelper("data",file_name)
        it = 0
        resolution_temperatures = 0     
        for row in csv_helper.data:
            if it == 0:
                resolution_temperatures \
                    = - cast.to_positive_int(row[0], "Elapsed time")
            if it == 1:
                resolution_temperatures += \
                    + cast.to_positive_int(row[0], "Elpased time")
            tmp_temperatures = []
            for col in row[1:]:
                value = cast.to_positive_float(col, "Temperatures")
                tmp_temperatures.append(value)
            self.temperatures.append(tmp_temperatures)
            it += 1
            
        self.cur_irradiances = self.irradiances[0]
        self.cur_temperatures = self.temperatures[0]
        
        self.forecast_horizon = parameters.get_parameter("forecast_horizon",
                                                         "int")
        
        cast = Cast("Normed rooftop PV output fit parameters")
        self.irwin_hall_factor = 0
        self.irwin_hall_factors = []
        file_name = "normed_rooftop_pv_output_fit_parameters.csv"
        csv_helper = CSVHelper("data",file_name)   
        it = 0
        resolution_fit = cast.to_positive_int(csv_helper.data[1][0],
                                              "Elapsed time") \
                         - cast.to_positive_int(csv_helper.data[0][0],
                                                "Elapsed time")
        for row in csv_helper.data:
            if self.clock.season_in_min["Start"] <= it * resolution_fit \
                < self.clock.season_in_min["End"]:
                time_factor = self.clock.time_step / 60
                if 60 % clock.time_step != 0:
                    raise RuntimeError("time_step do not add up to full hour!")
                z = 2/3 # a constant that was derived in the generator excel
                max_out = cast.to_positive_int(row[1], "Max output")
                s_p = cast.to_positive_float(row[11], "surf_po")
                s_c = cast.to_positive_float(row[12], "surf_co")
                self.irwin_hall_factors.append(time_factor * (s_c!=0) *max_out\
                                           * (1 + z * (1 - s_c / (s_p + s_c)))\
                                           / 1000)
            it += 1
        
        self.resolution_irradiance = resolution_irradiance
        self.resolution_temperatures = resolution_temperatures
        self.resolution_fit = resolution_fit
            
        self.forecast_mu, self.forecast_sig = 0.0, 0.0
        self.forecast_mu_po, self.forecast_sig_po_sqr = 0.0, 0.0
        self.max_output_co_sum, self.max_output_co_count = 0.0, 0
        for it, irwin_hall_factor in enumerate(self.irwin_hall_factors):
            if it * self.resolution_fit >= self.clock.forecast_horizon:
                break
            self.irwin_hall_factor += irwin_hall_factor
        
        # we use Irwin-Hall to derive normal distribution
        self.forecast_mu = self.irwin_hall_factor / 2
        self.forecast_sig = math.sqrt(self.irwin_hall_factor / 12)
        
    def step(self):
        cur_elapsed_time = self.clock.elapsed_time
        closest_time_record_irradiance \
            = int(round(cur_elapsed_time / self.resolution_irradiance, 0))
        closest_time_record_temperatures \
            = int(round(cur_elapsed_time / self.resolution_temperatures, 0))
        self.cur_irradiances = self.irradiances[closest_time_record_irradiance]
        self.cur_temperatures \
            = self.temperatures[closest_time_record_temperatures]
        
        if self.clock.elapsed_time != 0:
            cur_time = self.clock.elapsed_time
            horizon = self.clock.forecast_horizon
            time_step = self.clock.time_step
            prev_forecast_horizon_it = cur_time // time_step - 1
            next_forecast_horizon_it \
                = ( (cur_time + horizon) // time_step  \
                    -((cur_time + horizon) % time_step == 0) * 1 )
            self.irwin_hall_factor\
                += - self.irwin_hall_factors[prev_forecast_horizon_it] \
                   + self.irwin_hall_factors[next_forecast_horizon_it]
            self.forecast_mu = self.irwin_hall_factor / 2
            self.forecast_sig = math.sqrt(self.irwin_hall_factor / 12)
    
    def instantaneous_generation(self, pv_capacity):
        irradiance = random.choice(self.cur_irradiances)
        temperature = random.choice(self.cur_temperatures)
        
        # An x kW PV system refers to a PV system which under Standart Testing
        # Conditions (solar_irr = 1 kWm^-2, temp = 25°C) outputs x kW.
        # The equation to calculate PV output is:
        # P = efficiency * surface * solar_irr *( 1 - 0.005 * (temp - 25K))
        # Using this you can substitute efficiency * surface = x m^-2
        return pv_capacity * irradiance * (1 - 0.005 * (temperature - 25)) / 1000
    
    # TODO this neglects the PV capacity and return irradiation not pv power output! Needs to return power output
    def generation_forecast_distribution_parameter(self, name_plate_capacity):
        return self.forecast_mu * name_plate_capacity, \
                self.forecast_sig * name_plate_capacity
