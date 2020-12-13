# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 16:02:14 2020

@author: S3739258
"""

import sys
import random

from company import Company

class CompanyManager():
    """
    Holds all companies for easy access and simplified parameter adaptation.
    """
    def __init__(self, charger_manager, electricity_plan_manager):
        """
        Parameters
        ----------
        charger_manager : ChargerManager
            The instance of the charger manager used for the charging model.
        electricity_plan_manager : ElectricityPlanManager
            The instance of the electricity plan manager used for the charging
            model.

        Returns
        -------
        None.
        """
        self.companies = []
        self.charger_manager = charger_manager
        self.electricity_plan_manager = electricity_plan_manager
    
    def add_employee_to_location(self, location):
        add_to_new_company = False;
        pass # TODO Add criteria when new Company is created
        if len(self.companies) == 0:
            add_to_new_company = True
        
        company = Company()
        if add_to_new_company:
            uid = len(self.companies)
            
            if len(self.electricity_plan_manager.commercial_plan_uids) == 0:
                sys.exit("CompanyManager: No commercial electricity plans to"\
                         + "to choose from")
            # TODO Add criteria based on which electricity plan is chosen
            electricity_plan_uid \
                = random.choice(self.electricity_plan_manager.commercial_plan_uids)
            electricity_plan \
                = self.electricity_plan_manager.electricity_plans[electricity_plan_uid]
            
            charger_cost_per_kWh = 1 # TODO Add criteria for charger cost
            
            if len(self.charger_manager.charger_models) == 0:
                sys.exit("CompanyManager: No charger models to to choose from")
            
            # TODO Add criteria based on which the charger model is chosen
            charger_model_uid \
                = random.choice(self.charger_manager.commercial_model_uids)
            charger_model \
                = self.charger_manager.charger_models[charger_model_uid]
            
            employees_per_charger = 2 # TODO Add criteria to choose this ratio
            
            company = Company(uid, location, electricity_plan,
                              self.charger_manager, charger_cost_per_kWh,
                              charger_model, employees_per_charger)
            self.companies.append(company)
        else:
            company = random.choice(self.companies)
            
        company.add_employee()
        
        return company