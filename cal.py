# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 13:40:31 2021

@author: S3739258
"""

class Cal():
    def __init__(self, clock, location_road_manager, calendar_planer,
                 whereabouts, residency_location, employment_location,
                 cur_activity, cur_location,
                 distance_commuted_if_work_and_home_equal):
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
        self.cp = calendar_planer
        self.calendar = dict()
        self.whereabouts = whereabouts
        self.residency_location = residency_location
        self.employment_location = employment_location
        self.distance_commuted_if_work_and_home_equal \
            = distance_commuted_if_work_and_home_equal
        self.time_reserve = calendar_planer.arrival_time_reserve
        self.hours_worked_per_week \
            = calendar_planer.draw_hours_worked_per_week_at_random()
        
        self.cur_scheduled_activity = cur_activity
        self.cur_scheduled_location = cur_location
        self.cur_scheduled_activity_start_time = 0
        self.next_activity = None
        self.next_location = None
        self.next_departure_time = None
        self.next_activity_start_time = None
        self.next_route, self.next_route_length = None, None
    
    def generate_schedule(self):
        self.calendar, self.starts, self.ends = self.cp.create_calendar(self.hours_worked_per_week)
        self.cur_scheduled_activity = self.calendar[self.clock.elapsed_time]
        if self.cur_scheduled_activity == self.cp.HOME:
            self.cur_scheduled_location = self.residency_location
        else:
            self.cur_scheduled_location = self.employment_location
        self.next_activity, self.next_location, self.next_activity_start_time \
            = self.find_next_activity()
        self.next_route, self.next_route_length = self.find_next_route()
        self.next_departure_time = self.find_next_departure_time()
    
    def find_next_activity(self):
        """
        Finds the next planned activity different from the current activity.

        Returns
        -------
        next_activity : int
            See description above.
        next_location : Location
            Location corresponding to next_activity.
        next_location_arrival_time : int
            Time in minutes noted for arrival at the next location.

        """
        checked_time = self.clock.elapsed_time
        checked_weekly_time = self.clock.time_of_week
        start_time_of_the_week = self.clock.time_of_week
        
        cur_activity = self.cur_scheduled_activity
        next_activity = self.calendar[checked_weekly_time]
        
        if cur_activity not in [self.cp.TRANSIT, self.cp.EMERGENCY_CHARGING]:
            while cur_activity == next_activity:
                checked_time += self.clock.time_step
                checked_weekly_time += self.clock.time_step
                if checked_weekly_time >= 60*24*7:
                    checked_weekly_time = checked_weekly_time % 60*24*7
                if checked_weekly_time == start_time_of_the_week:
                    raise RuntimeWarning("Agent does not never commute!")
                next_activity = self.calendar[checked_weekly_time]
                
            if next_activity == self.cp.HOME:
                next_location = self.residency_location
            elif next_activity == self.cp.WORK:
                next_location = self.employment_location
            else:
                raise RuntimeError("Cal.py: Next Activity not implemented!")
            return next_activity, next_location, checked_time
        else:
            return self.next_activity, self.next_location, \
                    self.next_activity_start_time        
    
    def find_next_route(self):
        route = self.lrm.calc_route(self.cur_scheduled_location,
                                        self.next_location)
        if len(route) >= 2:
            return route, self.lrm.calc_route_length(route)
        else:
            return route, self.distance_commuted_if_work_and_home_equal
    
    def find_next_departure_time(self):
        """
        Returns the time in minutes when a car_agent should depart.

        Returns
        -------
        rounded_departure_time : int
            See above

        """
        travel_time = self.lrm.estimated_travel_time_between_locations(
                            self.whereabouts.cur_location, self.next_location)
        departure_time = self.next_activity_start_time - travel_time \
            - self.time_reserve
        rounded_departure_time = (departure_time // self.clock.time_step) \
            * self.clock.time_step
        if self.next_activity == self.cp.WORK:
            return rounded_departure_time
        else:
            return self.next_activity_start_time
    
    def step(self):        
        if self.clock.elapsed_time >= self.next_activity_start_time:
            self.cur_scheduled_activity = self.next_activity
            self.cur_scheduled_location = self.next_location
            self.cur_scheduled_activity_start_time \
                = self.next_activity_start_time
            self.next_activity, self.next_location, \
                self.next_activity_start_time = self.find_next_activity()
            self.next_route, self.next_route_length = self.find_next_route()
            self.next_departure_time = self.find_next_departure_time()
            
    def __repr__(self):
        msg = ""
        
        prev_location = None
        start_time = None
        last_time = None
        for key in self.calendar:
            if prev_location == None:
                start_time = key
                prev_location = self.calendar[key]
            elif not self.calendar[key] == prev_location:
                msg += "From " + str(start_time) + " to " + str(last_time) \
                        + " @ " + prev_location.name + "\n"
                start_time = key
                prev_location = self.calendar[key]
            last_time = key
        msg += "From " + str(start_time) + " to " + str(last_time) \
                + " @ " + prev_location.name
                
        return msg