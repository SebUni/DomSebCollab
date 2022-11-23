# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 14:36:13 2020

@author: S3739258
"""
from cast import Cast
from csv_helper import CSVHelper

import random
from charger_model import ChargerModel
from charger import Charger
import gc


class ChargerManager():
    """
    Holds and allows for easy access to all created chargers models
    and chargers.
    """
    def __init__(self):
        self.HOME_CHARGER = "residential"
        self.WORK_CHARGER = "work"
        self.PUBLIC_CHARGER = "public"
        
        self.chargers = []
        self.charger_models = {self.HOME_CHARGER: [], self.WORK_CHARGER: [],
                               self.PUBLIC_CHARGER: []}
        self.load_charger_models()
    
    def load_charger_models(self):
        """
        Reads information on individual charger models from charger_models.csv.
        """
        cast = Cast("Charger Model")
        csv_helper = CSVHelper("data","charger_models.csv")
        for row in csv_helper.data:
            uid = cast.to_positive_int(row[0], "Uid")
            cast.uid = uid
            classification = row[1]
            ac_power = cast.to_positive_float(row[2], "AC Power")
            dc_power = cast.to_positive_float(row[3], "DC Power")
            
            cm = ChargerModel(uid, classification, ac_power, dc_power, self)
            self.charger_models[classification].append(cm)
    
    def add_charger(self, charger_model):
        new_charger_uid = len(self.chargers)
        charger = Charger(new_charger_uid, charger_model)
        self.chargers.append(charger)#
        return charger
        
    def draw_charger_at_random(self, charger_classification):
        return random.choice(self.charger_models[charger_classification])
    
    def clear(self):
        attrs = ["HOME_CHARGER", "WORK_CHARGER", "PUBLIC_CHARGER", "chargers",
                 "charger_models"]
        for attr in attrs:
            if hasattr(getattr(self, attr), "clear"):
                getattr(self, attr).clear()
            delattr(self, attr)
        gc.collect()