# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 14:04:29 2020

@author: S3739258
"""

import sys

class ChargerModel():
    """
    Information container for Charger Models, that is different types of
    Chargers.
    """
    def __init__(self, uid, classification, ac_power, dc_power):
        """
        Parameters
        ----------
        uid : int
            Unique Id of the charger model.
        classification : string
            Can either be "res"isdential or "com"mercial.
        power_ac : int
            AC charging power of the charger in Watt.
        power_dc : int
            DC charging power of the charger in Watt.

        Returns
        -------
        None.

        """
        self.uid = int(uid)
        if not str(classification) in ["res", "com"]:
            msg = "Error creating charger model: '" + str(classification)
            msg += "' is not a valid charger model"
            sys.exit(msg)
        self.classification = str(classification)
        self.power_ac = int(ac_power)
        self.power_dc = int(dc_power)
        
    def __repr__(self):
        msg = "Uid: " + str(self.uid) + "; "
        msg += "Classification: " + self.classification + "; "
        msg += "AC Power: " + str(self.power_ac / 1000) + " kW; "
        msg += "DC Power: " + str(self.power_dc / 1000) + " kW"
        
        return msg