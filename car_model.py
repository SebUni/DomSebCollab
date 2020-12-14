# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 11:32:16 2020

@author: S3739258
"""

import sys

class CarModel():
    """
    Stores all information on a type of car.
    """
    def __init__(self, uid, car_consumption, drag_coeff, frontal_area,
                 mass, battery_capacity, charger_capacity):
        """
        Parameters
        ----------
        uid : int
            Unique Id of car model.
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
        charger_capacity : float
            Capacity of the on-board charger of the car model in kW.

        Returns
        -------
        None.
        """
        self.uid = uid
        try:
            self.car_consumption = float(car_consumption)
        except ValueError:
            sys.exit("Car consumption of car model " + str(uid) \
                     + " is ill defined!")
        try:
            self.drag_coeff = float(drag_coeff)
        except ValueError:
            sys.exit("Drag coefficient of car model " + str(uid) \
                     + " is ill defined!")
        try:
            self.frontal_area = float(frontal_area)
        except ValueError:
            sys.exit("Frontal area of car model " + str(uid) \
                     + " is ill defined!")
        try:
            self.mass = float(mass)
        except ValueError:
            sys.exit("Mass of car model " + str(uid) \
                     + " is ill defined!")
        try:
            self.battery_capacity = battery_capacity
        except ValueError:
            sys.exit("Battery capacity of car model " + str(uid) \
                     + " is ill defined!")
        try:
            self.charger_capacity = charger_capacity
        except ValueError:
            sys.exit("Charger capacity of car model " + str(uid) \
                     + " is ill defined!")
        
    def instantaneous_consumption(self, velocity):
        """
        The consumption of the car model at a given velocity.

        Parameters
        ----------
        velocity : float
            Momentary consumption of the car model km/h.

        Returns
        -------
        The instantaneous consumption as a float in kWh/km.
        """
        consumption = 1 # TODO implement proper equation for conumption
        return consumption
    
    def __repr__(self):
        msg = "Uid: " + str(self.uid) + "\n"
        msg += "Consumption: " + str(self.car_consumption) + " kWh/km\n"
        msg += "Drag coeff: " + str(self.drag_coeff) + "\n"
        msg += "Frontal area: " + str(self.frontal_area) + " m^2\n"
        msg += "Mass: " + str(self.mass) + " kg\n"
        msg += "Battery Capcity: " + str(self.battery_capacity) + " kWh\n"
        msg += "Charger Capacity: " + str(self.charger_capacity) + " kW"
        
        return msg