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
    def __init__(self, parameters, location_road_manager):
        self.MANUFACTURER = "MANUFACTURER"
        self.FORMULA = "FORMULA"
        
        self.parameters = parameters
        self.lrm = location_road_manager
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
            charger_capacity_ac \
                = cast.to_positive_float(row[7], "Charger capacity AC")
            charger_capacity_dc \
                = cast.to_positive_float(row[8], "Charger capacity DC")
                
            cm = CarModel(uid, car_model_name, car_consumption, drag_coeff,
                          frontal_area, mass, battery_capacity,
                          charger_capacity_ac, charger_capacity_dc, 
                          self.parameters, self)
            self.car_models[uid] = cm
            
    def draw_car_model_at_random(self, residency_location, employment_location,
                                 distance_commuted_if_work_and_home_equal):
        """
        Returns a car model which was drawn at Random. Criterias such as
        weights are still to be determined.

        Returns
        -------
        CarModel.
        """
        reserve_range = self.parameters.get_parameter("reserve_range","int")
        reserve_speed = self.parameters.get_parameter("reserve_speed","int")
        minimum_relative_state_of_charge \
            = self.parameters.get_parameter("minimum_relative_state_of_charge",
                                            "float")
        reserve_power = 0
        commute_distance = None
        if residency_location != employment_location:
            commute_distance = self.lrm.calc_route_length(self.lrm.calc_route(\
                                    residency_location, employment_location))
        else:
            commute_distance = distance_commuted_if_work_and_home_equal
        
        if commute_distance > 55:
            test = 0
        
        battery_capacity = 0
        work_charging_rate = 0
        commute_consumption = 0
        car_model = None
        while battery_capacity * 0.6 <= commute_consumption * 2 \
            or work_charging_rate * 6 < commute_consumption:
            car_model = random.choice(list(self.car_models.values()))
            battery_capacity = car_model.battery_capacity
            work_charging_rate = car_model.charger_capacity_ac
            commute_consumption = commute_distance * car_model.car_consumption
        #                         * minimum_relative_state_of_charge)
        # while battery_capacity <= commute_consumption * 2 + reserve_power *1.1:
        #     car_model = random.choice(list(self.car_models.values()))
        #     battery_capacity = car_model.battery_capacity
        #     commute_consumption = commute_distance * car_model.car_consumption
        #     reserve_power = max(car_model.consumption(reserve_speed,
        #                                               reserve_range),
        #                         car_model.battery_capacity \
        #                         * minimum_relative_state_of_charge)
        
        return car_model
        
    def __repr__(self):
        msg = ""
        for car_model in self.car_models:
            msg += str(car_model) + "\n"
            
        return msg