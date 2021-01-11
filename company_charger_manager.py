# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 13:06:58 2020

@author: S3739258
"""

from collections import deque

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
        self.chargers_in_use_by_car_agent = dict()
        self.chargers_in_use_by_charger = dict()
        self.chargers_not_in_use = []
        self.charging_que = deque()
        
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
    
    def block_charger(self, car_agent, queuing):
        """
        Blocks one charger for the car_agent.

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
        if not len(self.chargers_not_in_use) == 0:
            charger = self.charger_not_in_use.pop()
            self.chargers_in_use_by_car_agent[car_agent] = charger
            self.chargers_in_use_by_charger[charger] = car_agent
        else:
            if queuing:
                self.charging_que.append(car_agent)
        
    def unblock_charger(self, car_agent):
        """
        Unblocks a currently blocked charger and - if another car agent is
        currently queuing - reassign the freed up charger.

        Parameters
        ----------
        car_agent : CarAgent
            The employee that is about to leave work.

        Returns
        -------
        None.

        """
        if car_agent in self.chargers_in_use_by_car_agent:
            charger = self.chargers_in_use_by_car_agent[car_agent]
            del self.chargers_in_use_by_car_agent[car_agent]
            del self.chargers_in_use_by_charger[charger]
            self.chargers_not_in_use.append(charger)
            # if charging que is not empty
            if self.charging_que:
                # retrieve next car agent to be charged, remove it from que and
                # block a charger for it
                car_agent = self.charging_que.popleft()
                self.block_charger(car_agent)