# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 12:11:49 2020

@author: S3739258
"""
import random

from cast import Cast
from csv_helper import CSVHelper

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
        cast = Cast("Car Model")
        self.car_models = dict()
        
        csv_helper = CSVHelper("data","car_models.csv")
        for row in csv_helper.data:
            uid = cast.to_positive_int(row[0], "Uid")
            cast.uid = uid
                
            car_model_name = str(row[1]).strip(" ").strip('"')
            car_consumption = cast.to_positive_float(row[2], "Car consumption")
            drag_coeff = cast.to_positive_float(row[3], "Drag coeff")
            frontal_area = cast.to_positive_float(row[4], "Frontal area")
            mass = cast.to_positive_float(row[5], "Mass")
            battery_capacity \
                = cast.to_positive_float(row[6], "Battery capacity")
            charger_capacity \
                = cast.to_positive_float(row[7], "Charger capacity")
                
            cm = CarModel(uid, car_model_name, car_consumption, drag_coeff,
                          frontal_area, mass, battery_capacity,
                          charger_capacity)
            self.car_models[uid] = cm
            
    def draw_car_model_at_random(self):
        """
        Returns a car model which was drawn at Random. Criterias such as
        weights are still to be determined.

        Returns
        -------
        CarModel.
        """
        # TODO determine criteria for draw
        return random.choice(list(self.car_models))
        
    def __repr__(self):
        msg = ""
        for car_model in self.car_models:
            msg += str(car_model) + "\n"
            
        return msg