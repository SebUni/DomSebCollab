# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 23:47:02 2020

@author: S3739258
"""

import sys

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
        self.elapsed_time = 0
        self.cur_time_step = 0;
        self.pre_heat_steps = parameters.get("pre_heat_steps", "int")
        self.is_pre_heated = False
        self.season = parameters.get("season","int")
        self.time_step = parameters.get("time_step","int")
        self.time_step_limit = parameters.get("time_step_limit", "int")
        self.forecast_horizon = parameters.get("forecast_horizon", "int")
        
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
        season_start_in_min = {0: 60*24*(31+28+31+30+31+30+31+31+30),
                               1: 60*24*(0),
                               2: 60*24*(31+28+31),
                               3: 60*24*(31+28+31+30+31+30)}
        next_season = self.season + 1 if self.season != 3 else 0
        self.season_in_min = {"Start":season_start_in_min[self.season],
                              "End":season_start_in_min[next_season]}
        if next_season == 1:
            self.season_in_min["End"] \
                = 60*24*(31+28+31+30+31+30+31+31+30+31+30+31)
        if not (0 <= self.season <= 3):
            sys.exit("Season ill defined. Must be in [0,3]")
        
    def calc_time_of_day(self):
        """ Calculates how many minutes have elapsed since the most recent
        mid-night. """
        return self.elapsed_time % (60*24)
    
    def calc_time_of_week(self):
        """ Calculates how many minutes have elapsed since the most recent
        Sunday to Monday mid-night. """
        return self.elapsed_time % (60*24*7)
        
    def step(self):
        """
        Elapses time by the defined time_step.

        Returns
        -------
        None.

        """
        self.cur_time_step += 1
        if self.cur_time_step >= self.pre_heat_steps:
            self.is_pre_heated = True
        if not self.first_step_call:
            self.elapsed_time += self.time_step
            self.time_of_day = self.calc_time_of_day()
            self.time_of_week = self.calc_time_of_week()
        else:
            self.first_step_call = False