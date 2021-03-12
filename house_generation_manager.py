# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 15:36:10 2021

@author: S3739258
"""

import random
import math

from cast import Cast
from csv_helper import CSVHelper

from generation_forecast import GenerationForecast

class HouseGenerationManager():
    def __init__(self, parameters, clock):
        self.clock = clock
                
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
                resolution_irradiance = resolution_irradiance \
                    + cast.to_positive_int(row[0], "Elapsed time")
            tmp_irradiances = []
            for col in row[1:]:
                value = cast.to_positive_float(col, "Solar irradiance")
                tmp_irradiances.append(value)
            self.irradiances.append(tmp_irradiances)
            it = it + 1
        
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
                resolution_temperatures = resolution_temperatures \
                    + cast.to_positive_int(row[0], "Elpased time")
            tmp_temperatures = []
            for col in row[1:]:
                value = cast.to_positive_float(col, "Temperatures")
                tmp_temperatures.append(value)
            self.temperatures.append(tmp_temperatures)
            it = it + 1
            
        self.cur_irradiances = self.irradiances[0]
        self.cur_temperatures = self.temperatures[0]
        
        self.forecast_horizon = parameters.get_parameter("forecast_horizon",
                                                         "int")
        
        cast = Cast("Normed rooftop PV output fit parameters")
        self.fit_data = []
        file_name = "normed_rooftop_pv_output_fit_parameters.csv"
        csv_helper = CSVHelper("data",file_name)   
        it = 0
        resolution_fit = 0       
        for row in csv_helper.data:
            if it == 0:
                resolution_fit \
                    = - cast.to_positive_int(row[0], "Elapsed time")
            if it == 1:
                resolution_fit = resolution_fit \
                    + cast.to_positive_int(row[0], "Elpased time")
            # elapsed_minutes = cast.to_positive_int(row[0], "Elapsed minutes")
            self.fit_data.append(GenerationForecast(self.clock, row))
            it = it + 1
        
        self.resolution_irradiance = resolution_irradiance
        self.resolution_temperatures = resolution_temperatures
        self.resolution_fit = resolution_fit
            
        self.forecast_mu, self.forecast_sig = 0.0, 0.0
        self.forecast_mu_po, self.forecast_sig_po_sqr = 0.0, 0.0
        self.max_output_co_sum, self.max_output_co_count = 0.0, 0
        for it, fit_data_point in enumerate(self.fit_data):
            if it * self.resolution_fit >= self.clock.forecast_horizon:
                break
            if fit_data_point.peak_dominates_constant():
                self.forecast_mu_po = self.forecast_mu_po +fit_data_point.mu_po
                self.forecast_sig_po_sqr = self.forecast_sig_po_sqr \
                    + fit_data_point.sig_po ** 2
            else:
                self.max_output_co_sum = self.max_output_co_sum \
                    + fit_data_point.max_output
                self.max_output_co_count = self.max_output_co_count + 1
        
        avg_max_output_co = 0
        if self.max_output_co_count != 0:
           avg_max_output_co \
               = self.max_output_co_sum / self.max_output_co_count
        self.forecast_mu = self.forecast_mu_po + avg_max_output_co / 2
        forecast_sig_co_sqr = (avg_max_output_co / 12) ** 2
        self.forecast_sig \
            = math.sqrt(self.forecast_sig_po_sqr + forecast_sig_co_sqr)
        
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
                
            pf_prm = self.fit_data[prev_forecast_horizon_it]
            nf_prm = self.fit_data[next_forecast_horizon_it]
            if pf_prm.peak_dominates_constant():
                self.forecast_mu_po = self.forecast_mu_po - pf_prm.mu_po
                self.forecast_sig_po_sqr = self.forecast_sig_po_sqr \
                    - pf_prm.sig_po ** 2
            else:
                self.max_output_co_sum = self.max_output_co_sum \
                    - pf_prm.max_output
                self.max_output_co_count = self.max_output_co_count - 1
            if nf_prm.peak_dominates_constant():
                self.forecast_mu_po = self.forecast_mu_po + nf_prm.mu_po
                self.forecast_sig_po_sqr = self.forecast_sig_po_sqr \
                    + nf_prm.sig_po ** 2
            else:
                self.max_output_co_sum = self.max_output_co_sum \
                    + nf_prm.max_output
                self.max_output_co_count = self.max_output_co_count + 1
                
            avg_max_output_co = 0
            if self.max_output_co_count != 0:
               avg_max_output_co \
                   = self.max_output_co_sum / self.max_output_co_count
            self.forecast_mu = self.forecast_mu_po + avg_max_output_co / 2
            forecast_sig_co_sqr = (avg_max_output_co / 12) ** 2
            self.forecast_sig \
                = math.sqrt(self.forecast_sig_po_sqr + forecast_sig_co_sqr)
    
    def instantaneous_generation(self, pv_capacity):
        irradiance = random.choice(self.cur_irradiances)
        temperature = random.choice(self.cur_temperatures)
        
        # An x kW PV system refers to a PV system which under Standart Testing
        # Conditions (solar_irr = 1 kWm^-2, temp = 25°C) outputs x kW.
        # The equation to calculate PV output is:
        # P = efficiency * surface * solar_irr *( 1 - 0.05 * (temp - 25K))
        # Using this you can substitute efficiency * surface = x m^-2
        return pv_capacity * irradiance * (1 - 0.05 * (temperature - 25))
    
    def generation_forecast_distribution_parameter(self):
        return self.forecast_mu, self.forecast_sig
        