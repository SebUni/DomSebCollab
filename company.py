# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 13:26:10 2020

@author: S3739258
"""

import sys

class Company():
    """
    A company is either the place of employement for an agent or it can provide
    public chargers for a location.
    """
    def __init__(self, uid=None, location=None, electricity_plan=None,
                 charger_manager=None, charger_cost_per_kWh=None,
                 charger_model=None, employees_per_charger=None):
        """
        Parameters
        ----------
        uid : int
            Unique Id of the company.
        location : Location
            Location where the company is located. Not sure if needed but does
            not hurt to store this information piece.
        electricity_plan : ElectricityPlan
            The electricity plan the company is one. This parameter is chosen
            by the CompanyManager based on the the location where the company
            is located.
        charger_manager : ChargerManager
            The instance of the charger manager used for the charging model.
        charger_cost_per_kWh : float
            The cost an agent pays for charging 1 kWh using company chargers.
        charger_model : ChargerModel
            Each comany uses only the same type of charger models. This
            parameter determines which model it is.
        employees_per_charger : int
            Each company aquires enough chargers to satisfy the ratio of
            emplyees:chargers

        Returns
        -------
        None.
        """
        self.used_default_constructor = False
        if uid is None or location is None or electricity_plan is None \
            or charger_manager is None or charger_cost_per_kWh is None \
            or charger_model is None or employees_per_charger is None:
                self.used_default_constructor = True
        else:
            self.uid = uid
            self.location = location
            self.nbr_of_employees = 0
            self.chargers = []
            self.charger_cost_per_kWh = charger_cost_per_kWh
            self.electricity_plan = electricity_plan
            self.charger_manager = charger_manager
            self.charger_model = charger_model
            self.employees_per_charger = employees_per_charger
        
    def add_employee(self):
        """
        Adds the requirements to employee one extra agent at the company. That
        is especially to add enough chargers if the employee_per_charger ratio
        is undercut.

        Returns
        -------
        None.
        """
        if self.used_default_constructor:
            sys.exit("Tried to access company which was created with default"
                     + " constructor")
        self.nbr_of_employees += 1
        divisor = 1 if len(self.chargers) == 0 else len(self.chargers)
        cur_employees_per_charger = self.nbr_of_employees / divisor
        if cur_employees_per_charger > self.employees_per_charger\
            or self.nbr_of_employees == 1:
                charger = self.charger_manager.add_charger(self.charger_model)
                self.chargers.append(charger)
            
    def step(self):
        if self.used_default_constructor:
            sys.exit("Tried to access company which was created with default"
                     + " constructor")
        pass # TODO implement dynamics for companies
    
    def __repr__(self):
        msg = ""
        if not self.used_default_constructor:
            msg = "Uid: " + str(self.uid) + "\n"
            msg += "Location: " + str(self.location) + "\n"
            msg += "Chargers: " + str(self.chargers) + "\n"
            msg += "Cost per kWh: " + str(self.charger_cost_per_kWh) + "\n"
            msg += "Electricity plan: " + str(self.electricity_plan) + "\n"
            msg += "Charger Model: " + str(self.charger_model) + "\n"
            msg += "Nbr of employees: " + str(self.nbr_of_employees) + "\n"
            msg += "Employees per charger: " + str(self.employees_per_charger)
        else:
            msg = "Company initiated with default constructor."
            
        return msg