# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 15:36:10 2021

@author: S3739258
"""

import random

from cast import Cast
from csv_helper import CSVHelper

class HouseGenerationManager():
    def __init__(self, clock):
        self.clock = clock
                
        cast = Cast("Solar Irradation")
        self.irradiances = dict()
        file_name = "solar_irradiance_" \
                    + self.clock.season_names[self.clock.season] + ".csv"
        csv_helper = CSVHelper("data",file_name)        
        for row in csv_helper.data:
            elapsed_minutes = -1
            tmp_irradiances = []
            for col in row:
                if elapsed_minutes == -1:
                    elapsed_minutes = cast.to_positive_int(col,
                                                           "Elapsed minutes")
                else:
                    irradiance = cast.to_positive_int(col,"Solar Irradiance")
                    tmp_irradiances.append(irradiance)
            self.irradiances[elapsed_minutes] = tmp_irradiances
        
        cast = Cast("Temperatures")
        self.temperatures = dict()
        file_name = "temperatures_" \
                    + self.clock.season_names[self.clock.season] + ".csv"
        csv_helper = CSVHelper("data",file_name)        
        for row in csv_helper.data:
            elapsed_minutes = -1
            tmp_temperatures = []
            for col in row:
                if elapsed_minutes == -1:
                    elapsed_minutes = cast.to_positive_int(col,
                                                           "Elapsed minutes")
                else:
                    temperature = cast.to_float(col, "Temperatures")
                    tmp_temperatures.append(temperature)
            self.temperatures[elapsed_minutes] = tmp_temperatures
            
        self.cur_irradiances = self.irradiances[0]
        self.cur_temperatures = self.temperatures[0]
        
        elapsed_times = list(self.irradiances.keys())
        self.resolution = elapsed_times[1] - elapsed_times[0]
        
    def step(self):
        cur_elapsed_time = self.clock.elapsed_time
        closest_time_record \
            = int(round(cur_elapsed_time / self.resolution, 0))*self.resolution
        self.cur_irradiances = self.irradiances[closest_time_record]
        self.cur_temperatures = self.temperatures[closest_time_record]
    
    def instantaneous_generation(self, pv_capacity):
        irradiance = random.choice(self.cur_irradiances)
        temperature = random.choice(self.cur_temperatures)
        
        # An x kW PV system refers to a PV system which under Standart Testing
        # Conditions (solar_irr = 1 kWm^-2, temp = 25°C) outputs x kW.
        # The equation to calculate PV output is:
        # P = efficiency * surface * solar_irr *( 1 - 0.05 * (temp - 25K))
        # Using this you can substitute efficiency * surface = x m^-2
        return pv_capacity * irradiance * (1 - 0.05 * (temperature - 25))