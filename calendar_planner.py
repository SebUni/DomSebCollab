# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 14:34:59 2020

@author: S3739258
"""

class CalendarPlanner():
    """
    Creates the work schedules of all agents.
    """
    def __init__(self, clock, planning_horizon):
        """
        Der Konstruktor.

        Parameters
        ----------
        clock : Clock
            Needed for clock.time_step which is given in minutes.
        planning_horizon : int
            Defines how far ahead the agents' scheduldes shall be planned.
            Given in minutes.

        Returns
        -------
        None.

        """
        self.clock = clock
        self.planning_horizon = planning_horizon
        self.event_distribution = dict()
        
    def register_new_agent(self, car_agent):
        """ Registers car_agent for future planning. """
        self.event_distribution[car_agent] = []
    
    def plan_schedules(self):
        """ Updates the schedule of each registered CarAgent. """
        pass
        
    