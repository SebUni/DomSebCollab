# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 14:36:13 2020

@author: S3739258
"""
from cast import Cast
from csv_helper import CSVHelper

from charger_model import ChargerModel
from charger import Charger


class ChargerManager():
    """
    Holds and allows for easy access to all created chargers models
    and chargers.
    """
    def __init__(self):
        self.charger_models = dict()
        self.chargers = []
        self.commercial_model_uids = []
        self.residential_model_uids = []
        self.load_charger_models()
    
    def load_charger_models(self):
        """
        Reads information on individual charger models from charger_models.csv.
        """
        cast = Cast("Charger Model")
        self.charger_models = dict()
        csv_helper = CSVHelper("data","charger_models.csv")
        for row in csv_helper.data:
            uid = cast.to_positive_int(row[0], "Uid")
            cast.uid = uid
            classification = row[1]
            ac_power = cast.to_positive_int(row[2], "AC Power")
            dc_power = cast.to_positive_int(row[2], "DC Power")
            
            cm = ChargerModel(uid, classification, ac_power, dc_power)
            self.charger_models[uid] = cm
            if cm.classification == "com":
                self.commercial_model_uids.append(cm.uid)
            else:
                self.residential_model_uids.append(cm.uid)
    
    def add_charger(self, charger_model):
        new_charger_uid = len(self.chargers)
        charger = Charger(new_charger_uid, charger_model)
        self.chargers.append(charger)
        
        return charger