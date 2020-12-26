# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 14:34:59 2020

@author: S3739258
"""

class CalendarPlanner():
    """
    Creates the work schedules of all agents.
    """
    def __init__(self, clock, location_road_manager, planning_horizon):
        """
        Der Konstruktor.

        Parameters
        ----------
        clock : Clock
            Needed for clock.time_step which is given in minutes.
        location_road_manager : LocationRoadManager
            Handle to the location road manager.
        planning_horizon : int
            Defines how far ahead the agents' scheduldes shall be planned.
            Given in minutes.

        Returns
        -------
        None.

        """
        self.clock = clock
        self.lrm = location_road_manager
        self.planning_horizon = planning_horizon
        
    def create_calendar(self, car_agent):
        """
        Calculates the entries for one agent in self.event_distribution.
        """
        calendar = dict()
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        weekend_days = ["Sat", "Sun"]
        
        # TODO these need to be drawn at random from a yet to be determined
        #      distribution; best would be an extra function to jus that
        work_days = {"Mon", "Tue", "Wed", "Thu", "Fri"}
        start_time_weekdays = 9*60 # 9 o'clock AM
        start_time_weekends = 9*60 # 9 o'clock AM
        work_hours_per_week = 40*60 # 40 hours a week
        
        work_hours_per_day = work_hours_per_week / len(work_days)
        
        home_location = car_agent.house_agent.locations
        work_location = car_agent.company.location
        
        estimated_travel_time \
            = self.lrm.estimated_travel_time_between_locations(
                home_location, work_location)
        for time_slot in range(0, 60*24, self.clock.time_step):
            # Weekdays
            for i, day in enumerate(weekdays):
                if start_time_weekdays - estimated_travel_time < time_slot and\
                    time_slot < start_time_weekdays + work_hours_per_day and \
                    day in work_days:
                        calendar[time_slot+60*24*i] = work_location
                else:
                        calendar[time_slot+60*24*i] = home_location
            # Weekend days
            for i, day in enumerate(weekend_days):
                if start_time_weekends - estimated_travel_time < time_slot and\
                    time_slot < start_time_weekends + work_hours_per_day and \
                    day in work_days:
                        calendar[time_slot+60*24*(i+5)] = work_location
                else:
                        calendar[time_slot+60*24*(i+5)] = home_location
            
        return calendar