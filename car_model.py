# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 11:32:16 2020

@author: S3739258
"""

import math

class CarModel():
    """
    Stores all information on a type of car.
    """
    def __init__(self, uid, car_model_name, car_consumption, drag_coeff,
                 frontal_area, mass, battery_capacity, charger_capacity_ac,
                 charger_capacity_dc, parameters, car_model_manager):
        """
        Parameters
        ----------
        uid : int
            Unique Id of car model.
        car_model_name : string
            Name of Make and Model of the car.
        car_consumption : float
            Average consumption of car model in kWh/km.
        drag_coeff : float
            Drag coefficient.
        frontal_area : float
            Frontal area of the car model in m^2.
        mass : float
            Mass of the car in kg.
        battery_capacity : float
            Battery capacity of the car model in kWh.
        charger_capacity_ac : float
            Capacity of the on-board charger of the car model in kW.
        charger_capacity_dc : float
            Capacity of the on-board charger of the car model in kW.

        Returns
        -------
        None.
        """
        self.uid = uid
        self.car_model_name = car_model_name
        self.car_consumption = car_consumption
        self.drag_coeff = drag_coeff
        self.frontal_area = frontal_area
        self.mass = mass
        self.battery_capacity = battery_capacity
        self.charger_capacity_ac = charger_capacity_ac
        self.charger_capacity_dc = charger_capacity_dc
        self.consumption_calc_method \
            = parameters.get_parameter("consumption_calc_method","string")
        self.cmm = car_model_manager
        if self.consumption_calc_method not in [self.cmm.MANUFACTURER,
                                                self.cmm.FORMULA]:
            raise RuntimeError("car_model.py: consumption_calc_method is " \
                + "ill defined. '" + self.consumption_calc_method + "' is " \
                + "not implemented")
        
    def consumption(self, velocity, distance):
        if self.consumption_calc_method == self.cmm.FORMULA:
            time = velocity * distance
            inst_cons = self.instantaneous_consumption(velocity)
            return inst_cons * time
        if self.consumption_calc_method == self.cmm.MANUFACTURER:
            return self.car_consumption * distance
    
    def instantaneous_consumption(self, velocity):
        """
        The consumption in kWh of the car model at a given velocity.

        Parameters
        ----------
        velocity : float
            Momentary consumption of the car model km/h.

        Returns
        -------
        The instantaneous consumption as a float in kWh/km.
        """
        a = 0 # agent acceleration in m/s^2
        g = 9.81 # gravitational_acceleration in m/s^2
        alpha = 0 # road's gradient
        vel_ms = velocity / 3.6 # convert velocity to m/s from km/h
        # coefficient of rolling resistance of a tarmacadam road
        C = {"Car tire on smooth tamac road": 0.01,
             "Car tire on concrete road": 0.011,
             "Car tire on a rolled gravel road": 0.02,
             "Tarmacadam road": 0.025,
             "Unpaved road": 0.05} 
        consumption = self.mass * a * vel_ms \
            + self.mass * g * vel_ms * math.sin(alpha) \
            + self.mass * g * C["Car tire on concrete road"] * math.cos(alpha)\
            + 1/2 * self.drag_coeff * self.frontal_area * math.pow(vel_ms, 3)
        # equation above returns Watt but we need kW so:
        consumption /= 1000
        return consumption
    
    def __repr__(self):
        msg = "Uid: " + str(self.uid) + "\n"
        msg = "Make & Model: " + self.car_model_name + "\n"
        msg += "Consumption: " + str(self.car_consumption) + " kWh/km\n"
        msg += "Drag coeff: " + str(self.drag_coeff) + "\n"
        msg += "Frontal area: " + str(self.frontal_area) + " m^2\n"
        msg += "Mass: " + str(self.mass) + " kg\n"
        msg += "Battery Capcity: " + str(self.battery_capacity) + " kWh\n"
        msg += "Charger Capacity (AC/DV): " + str(self.charger_capacity_ac) \
                                + " / " + str(self.charger_capacity_dc) +" kW"
        
        return msg