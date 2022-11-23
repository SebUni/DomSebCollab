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
    def __init__(self, parameters, clock, charger_manager,
                 electricity_plan_manager, extracted_data):
        """
        Parameters
        ----------
        clock: Clock
            The instance of the clock module that provides information on time.
        charger_manager : ChargerManager
            The instance of the charger manager used for the charging model.
        electricity_plan_manager : ElectricityPlanManager
            The instance of the electricity plan manager used for the charging
            model.

        Returns
        -------
        None.
        """
        self.parameters = parameters
        self.companies = []
        self.clock = clock
        self.charger_manager = charger_manager
        self.electricity_plan_manager = electricity_plan_manager
        self.extracted_data = extracted_data
    
    def add_company(self, location):
        uid = len(self.companies)
        is_public_facility = True if len(location.companies) == 0 else False
        
        if len(self.electricity_plan_manager.commercial_plan_uids) == 0:
            sys.exit("CompanyManager: No commercial electricity plans to"\
                     + "to choose from")
        # TODO Add criteria based on which electricity plan is chosen
        electricity_plan_uid \
            = random.choice(self.electricity_plan_manager.commercial_plan_uids)
        electricity_plan \
            = self.electricity_plan_manager.electricity_plans[electricity_plan_uid]
            
        # TODO Add criteria for charger cost
        charger_cost_per_kWh, employees_per_charger, tracking_id = 0, 0, None
        if is_public_facility:
            charger_cost_per_kWh \
                = self.parameters.get("public_charger_cost_per_kWh", "float")
            employees_per_charger = 1
        else:                      # if company provides charging for employees
            charger_cost_per_kWh \
                = self.parameters.get("company_charger_cost_per_kWh", "float")
            employees_per_charger \
                = self.parameters.get("employees_per_charger", "positive_int")
            tracking_id = self.extracted_data.init_tracked_agent(uid)
            
        if len(self.charger_manager.charger_models) == 0:
            sys.exit("CompanyManager: No charger models to to choose from")
        
        charger_model = None
        if is_public_facility:
            charger_model \
                = self.charger_manager.draw_charger_at_random(\
                                        self.charger_manager.PUBLIC_CHARGER)
        else:
            charger_model \
                = self.charger_manager.draw_charger_at_random(\
                                        self.charger_manager.WORK_CHARGER)
            
        company = Company(uid, self.clock, tracking_id, location,
                          electricity_plan, self.charger_manager,
                          charger_cost_per_kWh, charger_model,
                          employees_per_charger, self.extracted_data)
        self.companies.append(company)
        location.companies.append(company)
        
        # add chargers to public charging company
        if is_public_facility:
            number_of_public_chargers \
                = self.parameters.get("number_of_public_chargers", "int")
            for i in range(number_of_public_chargers):
                company.ccm.add_charger()
        
        return company
        
    
    def add_employee_to_location(self, location):
        add_to_new_company = False;
        # TODO Add criteria when new Company is created
        pass 
        # if compares to == 1 not to == 0 to ignore the first company which
        # provides public charging for a location
        if len(location.companies) == 1:
            add_to_new_company = True
        
        company = Company()
        if add_to_new_company:
            company = self.add_company(location)
        else:
            company = random.choice(location.companies[1:])
            
        company.add_employee()
        
        return company
    
    def step(self):
        for company in self.companies:
            company.step()