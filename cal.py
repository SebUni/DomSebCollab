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
        # self.hours_worked_per_week = 60
        
        self.cur_scheduled_activity = cur_activity
        self.cur_scheduled_location = cur_location
        self.cur_scheduled_activity_start_time = 0
        self.next_activity = None
        self.next_location = None
        self.next_departure_time = None
        self.next_activity_start_time = None
        self.next_route, self.next_route_length = None, None
    
    def generate_schedule(self, min_shift_lengh):
        self.calendar, self.starts, self.ends \
            = self.cp.create_calendar(self.hours_worked_per_week,
                                      min_shift_lengh)
        if self.starts == [] and self.ends == []: return False
        self.cur_scheduled_activity = self.calendar[self.clock.elapsed_time]
        if self.cur_scheduled_activity == self.cp.HOME:
            self.cur_scheduled_location = self.residency_location
        else:
            self.cur_scheduled_location = self.employment_location
        self.next_activity, self.next_location, self.next_activity_start_time \
            = self.find_next_activity()
        self.next_route, self.next_route_length = self.find_next_route()
        self.next_departure_time = self.find_next_departure_time()
        return True
    
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
                            self.cur_scheduled_location, self.next_location)
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
            
    def find_next_departure_from_activity(self, activity):
        has_startet_activity = False
        test_time_of_week = self.clock.elapsed_time % (60*24*7)
        cur_location = None
        next_location = None
        while has_startet_activity == False \
            or self.calendar[test_time_of_week] == activity:
            test_time_of_week \
                = (test_time_of_week + self.clock.time_step) % (60*24*7)
            if self.calendar[test_time_of_week] == activity:
                has_startet_activity = True
                cur_location = self.location_from_activity(activity)
        
        if self.whereabouts.destination_activity == self.cp.HOME:
            next_activity = self.calendar[test_time_of_week]
            next_location = self.location_from_activity(next_activity)
            travel_time = self.lrm.estimated_travel_time_between_locations(
                                                cur_location, next_location)
            test_time_of_week -= travel_time + self.time_reserve
            test_time_of_week = (test_time_of_week // self.clock.time_step) \
                * self.clock.time_step
                
        return test_time_of_week
    
    def location_from_activity(self, activity):
        if activity == self.cp.HOME:
            return self.residency_location
        if activity == self.cp.WORK:
            return self.employment_location
        
        raise RuntimeError("cal.py: activity is not linked to a location!")
        return None
        
    def __repr__(self):
        msg = "hours_worked_per_week: {}\n".format(self.hours_worked_per_week)
        msg += "Starts: {}, Ends: {}\n".format(self.starts, self.ends)
        
        msg += "cur_sch_act/start_time: {} / {}\n".format(\
                                        self.cur_scheduled_activity,
                                        self.cur_scheduled_activity_start_time)
        msg += "next_act/start_time: {} / {}\n".format(self.next_activity,
                                                self.next_activity_start_time)
        msg += "next_dept_time: {}\n".format(self.next_departure_time)
        msg += "next_route: {}\n".format(self.next_route)
        msg += "next_route_length: {:.02f}".format(self.next_route_length)
        return msg