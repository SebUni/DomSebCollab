# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 13:26:10 2020

@author: S3739258
"""

import sys

from company_charger_manager import CompanyChargerManager

class Company():
    """
    A company is either the place of employement for an agent or it can provide
    public chargers for a location.
    """
    def __init__(self, uid=None, clock=None, location=None,
                 electricity_plan=None, charger_manager=None,
                 charger_cost_per_kWh=None, charger_model=None,
                 employees_per_charger=None):
        """
        Parameters
        ----------
        uid : int
            Unique Id of the company.
        clock: Clock
            The instance of the clock module that provides information on time.
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
        if uid is None or clock is None or location is None or \
            electricity_plan is None or charger_manager is None or \
            charger_cost_per_kWh is None or charger_model is None or \
            employees_per_charger is None:
                self.used_default_constructor = True
        else:
            self.uid = uid
            self.clock = clock
            self.location = location
            self.nbr_of_employees = 0
            self.ccm = CompanyChargerManager(charger_manager, charger_model)
            self.charger_cost_per_kWh = charger_cost_per_kWh
            self.electricity_plan = electricity_plan
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
        divisor = 1 if len(self.ccm.chargers) == 0 else len(self.ccm.chargers)
        cur_employees_per_charger = self.nbr_of_employees / divisor
        if cur_employees_per_charger > self.employees_per_charger\
            or self.nbr_of_employees == 1:
                self.ccm.add_charger()
                
    def charge_car(self, car_agent, charge_up_to):
        """
        Allow the car to charge at the house's charger.

        Parameters
        ----------
        car_agent : CarAgent
            The car_agent attempting to charge
        charge_up_to : float
            The amount of charge the car demands at most.
        car_charger_capacity : float
            Maximum charging rate of the car.

        Returns
        -------
        delivered_charge : float
            Amount of electricity in kWh provided to the car in this time step.
        charging_cost : float
            Cost in $ incurred for charing delivered_charge.

        """
        if self.used_default_constructor:
            sys.exit("Tried to access company which was created with default"
                     + " constructor")
        
        delivered_charge = 0.0
        charging_cost = 0.0
        
        if self.ccm.can_charge(car_agent):
            company_charger = self.ccm.chargers_in_use_by_car_agent[car_agent]
            charge_rate = max(min(car_agent.charger.charger_model.ac_power,
                                  company_charger.charger_model.ac_power),
                              min(car_agent.charger.charger_model.dc_power,
                                  company_charger.charger_model.dc_power))
        
            delivered_charge = min([self.clock.time_step / 60 * charge_rate,
                                charge_up_to])
            charging_cost = self.charger_cost_per_kWh * delivered_charge
        
        return delivered_charge, charging_cost
    
    def is_one_charger_available(self):
        """
        Checks if there is a charger currently not in use.

        Returns
        -------
        Bool
            As description above.

        """
        return len(self.ccm.chargers_not_in_use) != 0
    
    def can_charge(self, car_agent):
        """
        Checks if a car_agent is connected to one of the company's chargers.

        Parameters
        ----------
        car_agent : CarAgent
            The car agent to check for charger connectivity.

        Returns
        -------
        is_connected : bool.
            Feedback if the charger is connected.

        """
        return self.ccm.can_charge(car_agent)
    
    def block_charger(self, car_agent, queuing):
        """
        Attempts to blocks a currently unused charger for the car_agent.

        Parameters
        ----------
        car_agent : CarAgent
            The employee that just came for work.
        queuing: bool
            Informs the company charger manager that the car agent would like
            to join the que for charging. That is once a charger becomes
            available the car agent would like to use the freed up charger.

        Returns
        -------
        None.

        """
        self.ccm.block_charger(car_agent, queuing)
        
    def unblock_charger(self, car_agent):
        """
        Attepmts to unblock a currently blocked charger.

        Parameters
        ----------
        car_agent : CarAgent
            The employee that is about to leave work..

        Returns
        -------
        None.

        """
        self.ccm.unblock_charger(car_agent)
    
    def __repr__(self):
        msg = ""
        if not self.used_default_constructor:
            msg = "Uid: " + str(self.uid) + "\n"
            msg += "Location: " + str(self.location) + "\n"
            msg += "Cost per kWh: " + str(self.charger_cost_per_kWh) + "\n"
            msg += "Electricity plan: " + str(self.electricity_plan) + "\n"
            msg += "Nbr of employees: " + str(self.nbr_of_employees) + "\n"
            msg += "Employees per charger: " + str(self.employees_per_charger)
        else:
            msg = "Company initiated with default constructor."
            
        return msg