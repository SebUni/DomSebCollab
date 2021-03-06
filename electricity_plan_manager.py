# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 23:08:44 2020

@author: S3739258
"""
import sys
import random

from cast import Cast
from csv_helper import CSVHelper

from electricity_plan import ElectricityPlan

class ElectricityPlanManager():
    """
    Loads and holds all electricity plans for easy access.
    """
    def __init__(self, parameters, clock):
        """
        Parameters
        ----------
        clock : Clock
            The Handle to the global clock object.
        parameters: Parameters
            Provides external parameters.

        Returns
        -------
        None.
        """
        self.electricity_plans = dict()
        self.commercial_plan_uids = []
        self.residential_plan_uids = []
        self.load_electricity_plans(parameters, clock)
        
    def load_electricity_plans(self, parameters, clock):
        """
        Loads all electricity plans from electricity_plans.csv.

        Parameters
        ----------
        clock : Clock
            required for time_step parameter

        Returns
        -------
        None.
        """
        cast = Cast("Electricity Plan")
        self.electricity_plans = dict()
        csv_helper = CSVHelper("data","electricity_plans.csv")
        for row in csv_helper.data:
            uid = cast.to_positive_int(row[0], "Uid")
            cast.uid = uid
            classification = row[1]
            if not classification in ["res","com"]:
                sys.exit("Classification of electricity plan " + str(uid) \
                         + " is ill-defined!")
            is_commercial_plan = classification == "com"
            base = cast.to_float(row[2], "Base")
            feed_in_tariff = parameters.get_parameter("feed_in_tariff","float")
            # create tariff structure
            tariff_str = row[3]
            tariff = self.extract_tariffs_from_string(tariff_str)
            
            ep = ElectricityPlan(uid, is_commercial_plan, base, feed_in_tariff,
                                 tariff, clock.time_step)
            self.electricity_plans[uid] = ep
            if ep.is_commercial_plan:
                self.commercial_plan_uids.append(ep.uid)
            else:
                self.residential_plan_uids.append(ep.uid)
    
    def extract_tariffs_from_string(self, input_str):
        """
        Breaks down the tariff string imported from a electricity_plans.csv
        
        String must follow following syntax:
        tariff_start_time1:tariff_price1;tariff_start_time2:tariff_price2;\
        ...;tariff_start_timeN:tariff_priceN

        Caution: There is no trailing semni-collon!

        Parameters
        ----------
        input_str : string
            Must follow syntax as descirbed above.

        Returns
        -------
        tariffs : dict
            Returns tariff structure required for ElectricityPlan class.
        """
        tariffs = dict()
        tariffs_str = input_str.split(';')
        err_msg = "tariff_string '" + input_str + "' is ill-defined. \n\n"
        err_msg += "Use syntax 'start_time1:price1;...;start_timeN:priceN'!"
        for tariff_str in tariffs_str:
            tariff_str_split = tariff_str.split(':')
            try:
                tariff_start_time = int(tariff_str_split[0])
            except ValueError:
                sys.exit(err_msg)
            try:
                tariff_price = float(tariff_str_split[1])
            except:
                sys.exit(err_msg)
            tariffs[tariff_start_time] = tariff_price
        return tariffs
    
    def pick_plan_at_random(self, is_commercial_plan):
        """
        Returns an ElectricityPlan drawn at random. It can be determined if it
        should be a residential or a commercial plan.

        Parameters
        ----------
        is_commercial_plan : boolean
            Allows for choice between commercial and residential plans.

        Returns
        -------
        ElectricityPlan
            As explained above.

        """
        uid = 0
        if is_commercial_plan:
            uid = random.choice(self.commercial_plan_uids)
        else:
            uid = random.choice(self.residential_plans_uids)
        return self.electricity_plans[uid]
    
    def __repr__(self):
        msg = "Currently the following electricity plans are stored:"
        if len(self.electricity_plans) == 0:
            msg += "\n   No electricity plans stored!"
        for electricity_plan in self.electricity_plans.values():
            msg += "\n" + str(electricity_plan)
            
        return msg