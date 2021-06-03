# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 23:47:02 2020

@author: S3739258
"""

import sys

from console_output import ConsoleOutput

class Clock():
    """
    This object is used to have syncronised time in all other objects.
    """
    def __init__(self, parameters):
        """
        Well it creates the clock object.

        Parameters
        ----------
        time_step: int
            Length of each time step in minutes.
            
        time_step_limit: int
            Amount of time steps executed before simulation termination.
            
        season: int
            See season_name dict for definition.
        Returns
        -------
        None.

        """
        co = ConsoleOutput()
        self.elapsed_time = 0
        self.cur_time_step = 0;
        self.season = parameters.get_parameter("season","int")
        self.time_step = parameters.get_parameter("time_step","int")
        self.time_step_limit = parameters.get_parameter("time_step_limit",
                                                        "int")
        self.forecast_horizon = parameters.get_parameter("forecast_horizon",
                                                         "int")
        co.t_print("Selected time step: " + str(self.time_step) + " min")
        
        # This boolean indicates if step() has ever been called. If not the
        # clock does not step forward. This is done so that the first round can
        # be initalised with clock.step() to receive the right time. In turn,
        # this is done so that by the end of each step() the time safed in
        # clock is still the correct time of the current round.
        self.first_step_call = True
        
        self.time_of_day = self.calc_time_of_day()
        self.time_of_week = self.calc_time_of_week()
        self.season_names = {0 : "spring",
                             1 : "summer",
                             2 : "autumn",
                             3 : "winter"}
        if 0 <= self.season <= 3:
            co.t_print("Selected season: " + self.season_names[self.season])
        else:
            sys.exit("Season ill defined. Must be in [0,3]")
        
    def calc_time_of_day(self):
        """ Calculates how many minutes have elapsed since the most recent
        mid-night. """
        
        minutes_in_a_day = 60*24
        time_of_day = self.elapsed_time
        if time_of_day < 0:
            time_of_day += minutes_in_a_day
        time_of_day = time_of_day % minutes_in_a_day
            
            
        return time_of_day
    
    def calc_time_of_week(self):
        """ Calculates how many minutes have elapsed since the most recent
        Sunday to Monday mid-night. """
        
        minutes_in_a_week = 60*24*7
        time_of_week = self.elapsed_time
        if time_of_week < 0:
            time_of_week += minutes_in_a_week
        time_of_week = time_of_week % minutes_in_a_week
            
        return time_of_week
        
    def step(self):
        """
        Elapses time by the defined time_step.

        Returns
        -------
        None.

        """
        self.cur_time_step += 1
        if not self.first_step_call:
            self.elapsed_time += self.time_step
            self.time_of_day = self.calc_time_of_day()
            self.time_of_week = self.calc_time_of_week()
        else:
            self.first_step_call = False