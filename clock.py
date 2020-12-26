# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 23:47:02 2020

@author: S3739258
"""

class Clock():
    """
    This object is used to have syncronised time in all other objects.
    """
    def __init__(self, time_step):
        """
        Well it creates the clock object.
        
        Starts at -time_step so that the first round can be initalised with
        clock.step() to receive the right time. This is done so that by the end
        of each step() the time safed in clock is still the correct time of the
        current round.

        Parameters
        ----------
        time_step : int
            Length of each time step in minutes.

        Returns
        -------
        None.

        """
        self.elapsed_time = - time_step
        self.time_step = time_step
        self.time_of_day = self.calc_time_of_day()
        
    def calc_time_of_day(self):
        """ Calculates how many minutes have elapsed since the most recent
        mid-night. """
        
        minutes_in_a_day = 60*24
        time_of_day = self.elapsed_time
        while time_of_day < 0:
            time_of_day += minutes_in_a_day
        while time_of_day >= minutes_in_a_day:
            time_of_day -= minutes_in_a_day
            
        return time_of_day
        
    def step(self):
        """
        Elapses time by the defined time_step.

        Returns
        -------
        None.

        """
        self.elapsed_time += self.time_step