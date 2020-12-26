# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 13:06:58 2020

@author: S3739258
"""

class CompanyChargerManager():
    """ Keeps track of which charger a company owns and which of them are in
    use. """
    def __init__(self, charger_manager, charger_model):
        """
        El Constructor

        Parameters
        ----------
        charger_manager : ChargerManager
            The instance of the charger manager used for the charging model.
        charger_model : ChargerModel
            Each comany uses only the same type of charger models. This
            parameter determines which model it is.

        Returns
        -------
        None.

        """
        self.chargers = []
        self.charger_manager = charger_manager
        self.charger_model = charger_model
        self.chargers_in_use_by_car_agent = {}
        self.chargers_in_use_by_charger = {}
        self.chargers_not_in_use = []
        
    def add_charger(self):
        """ Adds one charger of type self.charger_model to the company. """
        charger = self.charger_manager.add_charger(self.charger_model)
        self.chargers.append(charger)
        # the cat coded again:
        # self.charger_not_in_use.append(charger)cvffffffffffcxxxxx 
        self.charger_not_in_use.append(charger)
        
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
        return car_agent in self.chargers_in_use_by_car_agent
    
    def block_charger(self, car_agent):
        """
        Blocks one charger for the car_agent.

        Parameters
        ----------
        car_agent : CarAgent
            The employee that just came for work.

        Returns
        -------
        None.

        """
        if not len(self.chargers_not_in_use) == 0:
            charger = self.charger_not_in_use.pop()
            self.chargers_in_use_by_car_agent[car_agent] = charger
            self.chargers_in_use_by_charger[charger] = car_agent
        
    def unblock_charger(self, car_agent):
        """
        Unblocks a currently blocked charger.

        Parameters
        ----------
        car_agent : CarAgent
            The employee that is about to leave work..

        Returns
        -------
        None.

        """
        if self.chargers_in_use_by_car_agent[car_agent] is not None:
            charger = self.chargers_in_use_by_car_agent[car_agent]
            self.chargers_in_use_by_car_agent.pop(car_agent)
            self.chargers_in_use_by_charger.pop(charger)
            self.chargers_not_in_use.append(charger)