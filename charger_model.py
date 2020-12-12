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
    def __init__(self, uid, classification, power):
        """
        Parameters
        ----------
        uid : int
            Unique Id of the charger model.
        classification : string
            Can either be "res"isdential, "com"mercial or "pub"lic.
        power : int
            Charging power of the charger in Watt.

        Returns
        -------
        None.

        """
        try:
            self.uid = int(uid)
        except ValueError:
            sys.exit("Uid of charger model is ill defined!")
        if not str(classification) in ["res", "com", "pub"]:
            msg = "Error creating charger model: '" + str(classification)
            msg += "' is not a valid charger model"
            sys.exit(msg)
        self.classification = str(classification)
        try:
            self.power = int(power)
        except ValueError:
            sys.exit("Power of charger model " + str(self.uid) \
                     + " is ill defined!")
        
    def __repr__(self):
        msg = "Uid: " + str(self.uid) + "; "
        msg += "Classification: " + self.classification + "; "
        msg += "Power: " + str(self.power / 1000) + " kW"
        
        return msg