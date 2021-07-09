# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 14:34:59 2020

@author: S3739258
"""

import random

from cast import Cast
from csv_helper import CSVHelper

def th(hour):
    if hour < 0:
        return hour + 168
    if hour >= 168:
        return hour - 168
    return hour

class CalendarPlanner():
    """
    Creates the work schedules of all agents.
    """
    def __init__(self, parameters, clock, location_road_manager):
        """
        Der Konstruktor.

        Parameters
        ----------
        parameters : Parameters
            Provides external parameters.
        clock : Clock
            Needed for clock.time_step which is given in minutes.
        location_road_manager : LocationRoadManager
            Handle to the location road manager.

        Returns
        -------
        None.

        """
        self.clock = clock
        self.lrm = location_road_manager
        self.arrival_time_reserve \
            = parameters.get_parameter("arrival_time_reserve", "int")
            
        self.min_hour_per_week = []
        self.max_hour_per_week = []
        self.hour_share_per_week = []
        self.load_hours_worked_per_week()
        
        self.total_hours_worked_per_week = 0
        
        self.distribution_weekly_work_hours = []
        self.load_distribution_weekly_work_hours()
        self.HOME = 0
        self.WORK = 1
        
    def create_calendar(self, hours_worked_per_week, home_location,
                        work_location):
        """
        Calculates the entries for one agent in self.event_distribution.
        """
        calendar = dict()
        
        starts, ends = self.generate_schedule(hours_worked_per_week)
        estimated_travel_time \
            = self.lrm.estimated_travel_time_between_locations(
                home_location, work_location)
        init_start = starts[0]
        for time_slot in range(0, 60*24*7, self.clock.time_step):
            if len(starts) != 0:
                if time_slot < starts[0] * 60 - estimated_travel_time:
                    calendar[time_slot] = self.HOME
                elif time_slot < ends[0] * 60:
                    calendar[time_slot] = self.WORK
                else:
                    calendar[time_slot] = self.HOME
                    starts = starts[1:]
                    ends = ends[1:]
            else:
                if time_slot >= (init_start + 168) * 60 - estimated_travel_time:
                    calendar[time_slot] = self.WORK
                else:
                    calendar[time_slot] = self.HOME
            
        return calendar
    
    def load_hours_worked_per_week(self):
        """
        Loads distrubtion on how many hours a person works per day.

        Returns
        -------
        None.
        """
        cast = Cast("Hours Worked Per Week")
        self.min_hour_per_week = []
        self.max_hour_per_week = []
        self.hour_share_per_week = []
        
        csv_helper = CSVHelper("data",
                               "share_of_total_shift_lengths_per_week.csv")
        for row in csv_helper.data:
            self.min_hour_per_week.append( \
                        cast.to_positive_int(row[0], "Min Hours Worked")) 
            self.max_hour_per_week.append( \
                        cast.to_positive_int(row[1], "Max Hours Worked")) 
            self.hour_share_per_week.append( \
                        cast.to_positive_float(row[2], "Hour Share Per Week"))
                
    def draw_hours_worked_per_week_at_random(self):
        choice = random.random()
        cum_share = 0
        chosen_it = 0
        for hour_share in self.hour_share_per_week:
            cum_share += hour_share
            if cum_share >= choice:
                break
            else:
                chosen_it += 1
        if chosen_it >= len(self.hour_share_per_week):
            chosen_it = len(self.hour_share_per_week) - 1
        
        chosen_hours_worked = random.randint(self.min_hour_per_week[chosen_it],
                                             self.max_hour_per_week[chosen_it])
        self.total_hours_worked_per_week += chosen_hours_worked
        
        return chosen_hours_worked
    
    def load_distribution_weekly_work_hours(self):
        """
        Loads distrubtion on how much a certain hour contributes to the total
        work performed per week.

        Returns
        -------
        None.
        """
        cast = Cast("Distribution of Weekly Work Hours")
        self.distribution_weekly_work_hours = []
        
        csv_helper = CSVHelper("data",
                    "share_of_total_hours_worked_per_hour_for_one_week.csv")
        for row in csv_helper.data:
            self.distribution_weekly_work_hours.append( \
                    cast.to_positive_float(row[1], "Share weekly work hours"))
                
    def prepare_schedule_generation(self):
        # hours worked per hour-time slot
        self.hours_weekly = []
        # percentage of 
        self.assigned_hour_share = []
        for hour_share in self.distribution_weekly_work_hours:
            self.hours_weekly.append(\
                                 hour_share * self.total_hours_worked_per_week)
            self.assigned_hour_share.append(0)
    
    def generate_schedule(self, hours_worked_per_week):
        srtd_indx = sorted(range(len(self.assigned_hour_share)),
                                 key=lambda k: self.assigned_hour_share[k],
                                 reverse=False)
        rest_between_shifts = 10
        max_shift_lengh = 12
        peak_dist = rest_between_shifts + max_shift_lengh
        slctd_pks = []
        i = 0
        largest_gap = 0
        max_attempts = 10000
        attempts = 0
        while len(slctd_pks) == 0 or largest_gap > 1 + 2 * rest_between_shifts:
            cur_pk = srtd_indx[i]
            is_close_to_other_peak = False
            for slctd_pk in slctd_pks:
                if slctd_pk - peak_dist < cur_pk < slctd_pk + peak_dist:
                    is_close_to_other_peak = True
                    break
            if not is_close_to_other_peak:
                slctd_pks.append(cur_pk)
            
            slctd_pks_srtd = slctd_pks.copy()
            slctd_pks_srtd.sort()
            
            largest_gap = 0
            for j in range(len(slctd_pks_srtd)):
                prev_j = j - 1
                offset = 0
                if j == 0:
                    prev_j = len(slctd_pks_srtd) - 1
                    offset = 168
                if slctd_pks_srtd[j] - slctd_pks_srtd[prev_j] + offset > largest_gap:
                    largest_gap = slctd_pks_srtd[j] - slctd_pks_srtd[prev_j] + offset
            i += 1
            if i == 168: break
            attempts += 1
            if attempts >= max_attempts:
                raise RuntimeError("Failed to create schedue. Please restart!")
        
        hours_remaining = hours_worked_per_week
        starts = []
        ends = []
        
        attempts = 0
        while hours_remaining != 0:
            scheduled_hour_successul = False
            best_start = 0
            best_start_it = -1
            best_end = 0
            best_end_it = -1
            for i in range(len(starts)):
                prev_i = i - 1
                if prev_i < 0: prev_i = len(ends) - 1
                next_i = i + 1
                if next_i == len(starts): next_i = 0
                
                dist_to_prev_shift = starts[i] - ends[prev_i]
                if dist_to_prev_shift < 0: dist_to_prev_shift += 168
                dist_to_next_shift =  starts[next_i] - ends[i]
                if dist_to_next_shift < 0: dist_to_next_shift += 168
                
                shift_length = ends[i] - starts[i]
                if shift_length < 0: shift_length += 168
                
                if dist_to_prev_shift > rest_between_shifts \
                    and shift_length < max_shift_lengh \
                    and (self.assigned_hour_share[th(starts[i] - 1)] < best_start \
                         or best_start_it == -1):
                        best_start = self.assigned_hour_share[th(starts[i] - 1)]
                        best_start_it = i
                if dist_to_next_shift > rest_between_shifts \
                    and shift_length < max_shift_lengh \
                    and (self.assigned_hour_share[th(ends[i] + 1)] < best_end \
                         or best_end_it == -1):
                        best_end = self.assigned_hour_share[th(ends[i] + 1)]
                        best_end_it = i
            best_new = 0
            best_new_it = -1
            for slctd_pk in slctd_pks:
                violates_dist_to_near_shifts = False
                for i in range(len(starts)):
                    prev_i = i - 1
                    if i < 0: prev_i = len(ends) - 1
                
                    dist_to_prev_shift = abs(slctd_pk - ends[prev_i])
                    dist_to_next_shift = abs(starts[i] - slctd_pk)
                    
                    if dist_to_next_shift < 10 or dist_to_prev_shift < rest_between_shifts \
                        or dist_to_next_shift > 168 - rest_between_shifts \
                        or dist_to_prev_shift > 168 - rest_between_shifts:
                        violates_dist_to_near_shifts = True
                    
                
                if not violates_dist_to_near_shifts \
                    and (self.assigned_hour_share[slctd_pk] < best_new \
                         or best_new_it == -1):
                    best_new = self.assigned_hour_share[slctd_pk]
                    best_new_it = slctd_pk
                    
            if len(starts) < 7 and best_new_it != -1 \
                and (best_new <= best_start or best_start_it == -1) \
                and (best_new <= best_end or best_end_it == -1):
                starts.append(best_new_it)
                ends.append(best_new_it)
                starts.sort()
                ends.sort()
                
                slctd_pks.remove(best_new_it)
                
                self.assigned_hour_share[th(best_new_it)] += 1 / self.hours_weekly[th(best_new_it)]
                scheduled_hour_successul = True
            elif best_start_it != -1 \
                and (best_end >= best_start or best_end_it == -1) \
                and (best_new >= best_start or best_new_it == -1 or len(starts) >= 7):
                starts[best_start_it] -= 1
                self.assigned_hour_share[th(starts[best_start_it])] \
                    += 1 / self.hours_weekly[th(starts[best_start_it])]
                hours_remaining -= 1
                scheduled_hour_successul = True
            elif best_end_it != -1 \
                and (best_start >= best_end or best_start_it == -1) \
                and (best_new >= best_end or best_new_it == -1 or len(starts) >= 7):
                ends[best_end_it] += 1
                self.assigned_hour_share[th(ends[best_end_it])] \
                    += 1 / self.hours_weekly[th(ends[best_end_it])]
                hours_remaining -= 1
                scheduled_hour_successul = True
            else:
                largest_gap = 0
                largest_gap_center = -1
                for i in range(len(starts)):
                    prev_i = i - 1
                    offset = 0
                    if i == 0:
                        prev_i = len(starts) - 1
                        offset = 168
                    cur_gap = starts[i] - ends[prev_i] + offset
                    if cur_gap > largest_gap:
                        largest_gap = cur_gap
                        largest_gap_center = (starts[i] + ends[prev_i] - offset) // 2
                        if largest_gap_center < 0: largest_gap_center + offset
                if largest_gap > rest_between_shifts * 2:
                    slctd_pks.append(largest_gap_center)
                else:
                    slctd_pks = [12,36,60,84,108,132,156]
                    hours_remaining = hours_worked_per_week
                    starts = []
                    ends = []
            if not scheduled_hour_successul and len(starts) == 7:
                slctd_pks = [12,36,60,84,108,132,156]
                hours_remaining = hours_worked_per_week
                starts = []
                ends = []
                
        return starts, ends