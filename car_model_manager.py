# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 12:11:49 2020

@author: S3739258
"""

import csv
import sys

from car_model import CarModel

class CarModelManager():
    """
    Stores and holds all car models used in the simulation.
    """
    def __init__(self):
        self.car_models = dict()
        self.load_car_models()
        
    def load_car_models(self):
        """
        Loads all car models from car_models.csv.

        Returns
        -------
        None.
        """
        self.car_models = dict()

        with open('data\car_models.csv', newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                uid_str, car_consumption, drag_coeff = row[0], row[1], row[2]
                frontal_area, mass, battery_capacity = row[3], row[4], row[5]
                charger_capacity = row[6]
                # here only uid is checked for key of dict
                # data validity of rest is checked in CarModel-constructor
                try:
                    uid = int(uid_str)
                except ValueError:
                    sys.exit("Uid of charger model is ill defined!")
                cm = CarModel(uid, car_consumption, drag_coeff, frontal_area,
                              mass, battery_capacity, charger_capacity)
                self.car_models[uid] = cm
    
    def __repr__(self):
        msg = ""
        for car_model in self.car_models:
            msg += str(car_model) + "\n"
            
        return msg