# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 13:40:31 2021

@author: S3739258
"""

class Cal():
    def __init__(self, clock, location_road_manager, calendar_planer,
                 whereabouts, residency_location, employment_location):
        """
        Well it's a constructor'

        Parameters
        ----------
        clock : Clock
        location_road_manager : LocationRoadManager
        calendar_planer : CalendarPlaner
        whereabouts : Whereabouts
            Whereabouts of the car_agent associated with this calendar.
        residency_location : Location
            ... of the car_agent associated with this calendar.
        employment_location : Location
            ... of the car_agent associated with this calendar.

        Returns
        -------
        None.

        """
        self.clock = clock
        self.lrm = location_road_manager
        self.calendar = calendar_planer.create_calendar(residency_location,
                                                        employment_location)
        self.whereabouts = whereabouts
        self.residency_location = residency_location
        self.employment_location = employment_location
        self.time_reserve = calendar_planer.arrival_time_reserve
        
        self.cur_scheduled_location = self.calendar[clock.elapsed_time]
        self.next_location, self.next_location_arrival_time \
            = self.find_next_location()
        self.next_route, self.next_route_length = self.find_next_route()
        self.upcoming_departure_time = self.find_upcoming_departure_time()
    
    def find_next_location(self):
        """
        Finds the next planned location different from the current location.

        Returns
        -------
        next_location : Location
            See description above.
        next_location_arrival_time : int
            Time in minutes noted for arrival at the next location.

        """
        if self.employment_location != self.residency_location:
            next_location = self.whereabouts.cur_location
            checked_time = self.clock.time_of_week
            checked_weekly_time = checked_time
            while self.whereabouts.cur_location == next_location:
                checked_time += self.clock.time_step
                checked_weekly_time += self.clock.time_step
                if checked_weekly_time >= 60*24*7:
                    checked_weekly_time = checked_weekly_time % 60*24*7
                next_location = self.calendar[checked_weekly_time]
            return next_location, checked_time
        else:
            return self.residency_location, \
                    (self.clock.time_step_limit + 1) * self.clock.time_step
    
    def find_next_route(self):
        if self.whereabouts.cur_location != self.next_location:
            route = self.lrm.calc_route(self.whereabouts.cur_location,
                                        self.next_location)
            return route, self.lrm.calc_route_length(route)
        else:
            return [], 0
    
    def find_upcoming_departure_time(self):
        """
        Returns the time in minutes when a car_agent should depart.

        Returns
        -------
        rounded_departure_time : int
            See above

        """
        travel_time = self.lrm.estimated_travel_time_between_locations(
                            self.whereabouts.cur_location, self.next_location)
        departure_time = self.next_location_arrival_time - travel_time \
            - self.time_reserve
        rounded_departure_time = (departure_time // self.clock.time_step) \
            * self.clock.time_step
        return rounded_departure_time
    
    def step(self):
        if self.whereabouts.cur_location == self.next_location \
            or self.clock.elapsed_time >= self.next_location_arrival_time:
        
            self.next_location, self.next_location_arrival_time \
                = self.find_next_location()
            self.next_route = self.find_next_route()
            self.upcoming_departure_time = self.find_upcoming_departure_time()