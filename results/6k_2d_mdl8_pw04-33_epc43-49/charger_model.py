# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 14:04:29 2020

@author: S3739258
"""

class ChargerModel():
    """
    Information container for Charger Models, that is different types of
    Chargers.
    """
    def __init__(self, uid, classification, ac_power, dc_power,
                 charger_manager):
        """
        Parameters
        ----------
        uid : int
            Unique Id of the charger model.
        classification : string
            Types as defined in charger_manager
        power_ac : int
            AC charging power of the charger in KiloWatt.
        power_dc : int
            DC charging power of the charger in KiloWatt.

        Returns
        -------
        None.

        """
        self.uid = int(uid)
        if not str(classification) in [charger_manager.HOME_CHARGER,
                                       charger_manager.WORK_CHARGER,
                                       charger_manager.PUBLIC_CHARGER]:
            msg = "charger_model.py: Error creating charger model: '" \
                + str(classification) + "' is not a valid charger model!"
            raise RuntimeError(msg)
        self.classification = str(classification)
        self.power_ac = float(ac_power)
        self.power_dc = float(dc_power)
        
    def __repr__(self):
        msg = "Uid: " + str(self.uid) + "; "
        msg += "Classification: " + self.classification + "; "
        msg += "AC Power: " + str(self.power_ac) + " kW; "
        msg += "DC Power: " + str(self.power_dc) + " kW"
        
        return msg