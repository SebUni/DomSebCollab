# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 14:24:22 2020

@author: S3739258
"""

class Charger():
    """
    Individual charger used to recharge EV.
    """
    def __init__(self, uid, charger_model):
        """
        Parameters
        ----------
        uid : int
            Unique Id of the charger.
        charger_model : ChargerModel
            Model of the charger.

        Returns
        -------
        None.

        """
        self.uid = uid
        self.charger_model = charger_model
        self.available = True
        
    def __repr__(self):
        msg = "Uid: " + str(self.uid) + "; "
        msg += "Available: " + str(self.available) + "; "
        msg += "Model: [" + str(self.charger_model) + "]"
        
        return msg