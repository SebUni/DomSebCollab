# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 17:01:55 2020

@author: S3739258
"""

import sys

class ElectricityPlan():
    """
    Container for data of an individual electricity plan.
    """
    def __init__(self, uid, is_commercial_plan, base, feed_in_tariff, tariff,
                 time_step):
        """
        Parameters
        ----------
        uid : int
            Unique Id of the electricity plan.
        is_commerical_plan : boolean
            Plans can either be residential or commercial.
        base : float
            Monthly base rate for a plan.
        feed_in_tariff : float
            Feed in tariff for feeding electricity into the grid.
        tariff : {start_time, cost_per_kWh}
            start_time given as int and noted in hours.
            cost_per_kWh is given in Dolars.
            First key requires start_time = 0.
            For example: {0: 0.40, 8: 0.50, 24: 0.40}
        time_step : int
            time_step given in minutes
        Returns
        -------
        None.

        """
        self.uid = uid
        self.is_commercial_plan = bool(is_commercial_plan)
        self.base = base
        self.tariff = dict()
        self.feed_in_tariff = feed_in_tariff
        # check that time_step is adequatly chosen
        if (24*60) % time_step != 0:
            sys.exit("time_step is not adequatly chosen!")
        for time_slot_start in range(0, 24*60, time_step):
            sum_tariff = 0.0
            sum_weight = 0
            time_slot_end = time_slot_start + time_step
            for tariff_start in list(tariff.keys()):
                tariff_end = 24*60 # next tariff start
                for sub_tariff_start in list(tariff.keys()):
                    if tariff_start < sub_tariff_start < tariff_end:
                        tariff_end = sub_tariff_start
        
                weight = 0
                if tariff_start <= time_slot_start < tariff_end < time_slot_end:
                    weight = (tariff_end - time_slot_start) / time_step
                if time_slot_start <= tariff_start < tariff_end <= time_slot_end:
                    weight = (time_slot_end - time_slot_start) / time_step
                if time_slot_start < tariff_start < time_slot_end <= tariff_end:
                    weight = (time_slot_end - tariff_start) / time_step
                if tariff_start <= time_slot_start < time_slot_end < tariff_end:
                    weight = 1
                if tariff_start < time_slot_start < time_slot_end <= tariff_end:
                    weight = 1
        
                sum_tariff += weight*tariff[tariff_start]
                sum_weight += weight
            self.tariff[time_slot_start] = sum_tariff / sum_weight
    
    def cost_of_use(self, used_kWh, time_of_use):
        """
        Calculates the price the consumer has to pay for consumed electricity.

        Parameters
        ----------
        used_kWh : float
            Consumed power.
        time_of_use : int
            Start time of the time of use interval, given in minutes since
            midnight.

        Returns
        -------
        float.
        """
        # Deactivate time of use 
        # return self.tariff[time_of_use]*used_kWh
        return self.tariff[0]*used_kWh
    
    def __repr__(self):
        msg = "Uid: " + str(self.uid) + "; "
        msg += "Is commerical plan: " + str(self.is_commercial_plan) + "; "
        msg += "Base fee: " + str(self.base)
        
        return msg