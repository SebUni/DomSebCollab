# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 14:36:13 2020

@author: S3739258
"""

import csv

from charger_model import ChargerModel
from charger import Charger
from cast import Cast

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
        with open('charger_models.csv', newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                uid = cast.to_positive_int(row[0], "Uid")
                cast.uid = uid
                classification = row[1]
                power = cast.to_positive_int(row[3], "Power")
                
                cm = ChargerModel(uid, classification, power)
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