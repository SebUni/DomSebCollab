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
        self.TRANSIT = 0
        self.HOME = 1
        self.WORK = 2
        self.EMERGENCY_CHARGING = 3
        
    def create_calendar(self, hours_worked_per_week, min_shift_length):
        """
        Calculates the entries for one agent in self.event_distribution.
        """
        calendar = dict()
        
        starts, ends = self.generate_schedule(hours_worked_per_week,
                                              min_shift_length)
        starts_org, ends_orgs = starts, ends
        init_start = starts[0]
        for time_slot in range(0, 60*24*7, self.clock.time_step):
            if len(starts) != 0:
                if time_slot < starts[0] * 60:
                    calendar[time_slot] = self.HOME
                elif time_slot < ends[0] * 60:
                    calendar[time_slot] = self.WORK
                else:
                    calendar[time_slot] = self.HOME
                    starts = starts[1:]
                    ends = ends[1:]
            else:
                if time_slot >= (init_start + 168) * 60:
                    calendar[time_slot] = self.WORK
                else:
                    calendar[time_slot] = self.HOME
            
        return calendar, starts_org, ends_orgs
    
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
    
    def generate_schedule(self, hours_worked_per_week, min_shift_length):
        # parameters
        rest_between_shifts = 10
        max_shift_lengh = 12
        # adjust input if needed
        max_shift_length_limit = max_shift_lengh / 2
        min_shift_length = min(min_shift_length, hours_worked_per_week,
                               max_shift_length_limit)
        peak_distance = rest_between_shifts + max_shift_lengh
        selected_peaks = []
        # creates a list which sorts all hours of the week according to the
        # relative amount of shifts covering this hour in descending order 
        # in descending order
        sorted_index \
            = sorted(range(len(self.assigned_hour_share)),
                               key=lambda k: (self.assigned_hour_share[k],
                                    - self.distribution_weekly_work_hours[k]))
        # search all hours of the week for best places, that is the hours which
        # exhibit the lowest relative shift coverage to spawn a new shift at
        for hour_it in range(7*24):
            cur_hour = sorted_index[hour_it]
            # determine next best hour to create a shift which is far enough
            # away from other shift spawn points
            is_close_to_other_peak = False
            for selected_peak in selected_peaks:
                if selected_peak - peak_distance < cur_hour \
                    < selected_peak + peak_distance:
                    is_close_to_other_peak = True
                    break
            if not is_close_to_other_peak:
                selected_peaks.append(cur_hour)
            
            # bring all peak in chronological order
            selected_peaks_sorted = selected_peaks.copy()
            selected_peaks_sorted.sort()
            
            # stop the search for new shift spawn points if next spawn point
            # would be to close to already selected shift spawn points
            largest_gap = 0
            for peak_it in range(len(selected_peaks_sorted)):
                prev_peak_it = peak_it - 1
                offset = 0
                if peak_it == 0:
                    prev_peak_it = len(selected_peaks_sorted) - 1
                    offset = 168
                gap_to_prev_peak = selected_peaks_sorted[peak_it] \
                                   - selected_peaks_sorted[prev_peak_it]+offset
                if gap_to_prev_peak > largest_gap:
                    largest_gap = gap_to_prev_peak
            if largest_gap <= 1+2*rest_between_shifts:
                break
        
        # place hours for shifts
        starts, ends = [], []
        # create make shift for loop iterating over all hours, with iterator
        # cur_hour iterating upon successful placement of an hour in a shift
        cur_hour = 0
        while cur_hour < hours_worked_per_week:
            scheduled_hour_successul = False
            hours_needed_for_cur_shifts \
                = sum([max(min_shift_length-(ends[shift]-starts[shift])%168,0)\
                       for shift in range(len(starts))])
            remaining_hours_for_shift_extenstion \
                = sum([max_shift_lengh-(ends[shift] - starts[shift]) % 168 \
                       for shift in range(len(starts))])
            remaining_hours_for_agent = hours_worked_per_week - cur_hour
            # scan through all shifts to find the best places to start a shift
            # earlier and end a shift later
            best_start_main = 0 # = best_shift_to_start_earlier_rel_coverage
            best_start_aux = 0  # = best_shift_to_start_earlier_rel_work_hours
            best_start_it = -1  # = best_shift_to_start_earlier
            best_end_main = 0   # = best_shift_to_end_later_rel_coverage
            best_end_aux = 0    # = best_shift_to_end_later_rel_work_hours
            best_end_it = -1    # = best_shift_to_end_later
            # as shifts are stored in the lists 'starts' and 'ends' range
            # depends on their length
            for shift in range(len(starts)):
                # modulus ensures that iterator stays with in the starts / ends
                # interval
                prev_shift = (shift - 1) % len(ends)
                next_shift = (shift + 1) % len(starts)
                # modulus ensures that distances and shift length are adapted
                # for shifts that cover a night from Sunday to Monday
                distance_to_prev_shift = (starts[shift] - ends[prev_shift])%168
                distance_to_next_shift = (starts[next_shift] - ends[shift])%168
                shift_length = (ends[shift] - starts[shift]) % 168
                if remaining_hours_for_shift_extenstion \
                    < remaining_hours_for_agent: break
                if shift_length >= min_shift_length \
                    and hours_needed_for_cur_shifts == remaining_hours_for_agent:
                    continue
                assigned_hour_share \
                    = self.assigned_hour_share[(starts[shift] - 1) % 168]
                distribution_weekly_work_hours \
                    = self.distribution_weekly_work_hours[(starts[shift]-1)%168]
                if distance_to_prev_shift > rest_between_shifts \
                    and shift_length < max_shift_lengh \
                    and (assigned_hour_share < best_start_main \
                         or best_start_it == -1 or \
                         (assigned_hour_share == best_start_main \
                          and best_start_aux > distribution_weekly_work_hours)):
                    best_start_main = assigned_hour_share
                    best_start_aux  = distribution_weekly_work_hours
                    best_start_it = shift
                assigned_hour_share \
                    = self.assigned_hour_share[(ends[shift] + 1) % 168]
                distribution_weekly_work_hours \
                    = self.distribution_weekly_work_hours[(ends[shift]+1)%168]
                if distance_to_next_shift > rest_between_shifts \
                    and shift_length < max_shift_lengh \
                    and (assigned_hour_share < best_end_main \
                         or best_end_it == -1 or \
                         (assigned_hour_share == best_end_main \
                          and best_end_aux > distribution_weekly_work_hours)):
                    best_end_main = assigned_hour_share
                    best_end_aux = distribution_weekly_work_hours
                    best_end_it = shift
            # scan through all spawn places to find the best places for new a
            # new shift to startshifts 
            best_new_main = 0   # = best_hour_to_start_a_new_shift_rel_coverage
            best_new_aux = 0    # = best_hour_to_start_a_new_shift_rel_work_hours
            best_new_it = -1    # = best_hour_to_start_a_new_shift
            for cur_spawn_pos in selected_peaks:
                # only spawn new shift if there is enough hours remaining to 
                # ensure minimum shift length
                if remaining_hours_for_agent < min_shift_length: break
                #  
                if remaining_hours_for_agent \
                    < hours_needed_for_cur_shifts + min_shift_length: break
                # ensure new shift does not get to close to existing shifts
                violates_dist_to_near_shifts = False
                for shift in range(len(starts)):
                    prev_shift = (shift - 1) % len(ends)
                    dist_to_prev_shift = abs(cur_spawn_pos - ends[prev_shift])
                    dist_to_next_shift = abs(starts[shift] - cur_spawn_pos)
                    if dist_to_next_shift < rest_between_shifts\
                        or dist_to_prev_shift < rest_between_shifts \
                        or dist_to_next_shift > 168 - rest_between_shifts \
                        or dist_to_prev_shift > 168 - rest_between_shifts:
                        violates_dist_to_near_shifts = True
                    
                assigned_hour_share = self.assigned_hour_share[cur_spawn_pos]
                distribution_weekly_work_hours \
                    = self.distribution_weekly_work_hours[cur_spawn_pos]
                if not violates_dist_to_near_shifts \
                    and (assigned_hour_share < best_new_main \
                         or best_new_it == -1 or \
                         (assigned_hour_share == best_new_main \
                          and distribution_weekly_work_hours > best_new_aux)):
                    best_new_main = assigned_hour_share
                    best_new_aux = distribution_weekly_work_hours
                    best_new_it = cur_spawn_pos
                    
            if self.cmp(best_new_main, best_new_aux, (best_new_it != -1 and len(starts) < 7),
                        best_start_main, best_start_aux, best_start_it != -1,
                        best_end_main, best_end_aux, best_end_it != -1):
                starts.append(best_new_it)
                ends.append(best_new_it+1)
                starts.sort()
                ends.sort()
                
                selected_peaks.remove(best_new_it)
                
                self.assigned_hour_share[best_new_it % 168] \
                    += 1 / self.hours_weekly[best_new_it % 168]
                self.assigned_hour_share[(best_new_it + 1) % 168] \
                    += 1 / self.hours_weekly[(best_new_it + 1) % 168]
                cur_hour += 1
                scheduled_hour_successul = True
            elif self.cmp(best_start_main, best_start_aux, best_start_it != -1,
                          best_new_main, best_new_aux, (best_new_it != -1 and len(starts) < 7),
                          best_end_main, best_end_aux, best_end_it != -1):
                starts[best_start_it] -= 1
                self.assigned_hour_share[th(starts[best_start_it])] \
                    += 1 / self.hours_weekly[th(starts[best_start_it])]
                cur_hour += 1
                scheduled_hour_successul = True
            elif self.cmp(best_end_main, best_end_aux, best_end_it != -1,
                          best_start_main, best_start_aux, best_start_it != -1,
                          best_new_main, best_new_aux, (best_new_it != -1 and len(starts) < 7)):
                ends[best_end_it] += 1
                self.assigned_hour_share[th(ends[best_end_it])] \
                    += 1 / self.hours_weekly[th(ends[best_end_it])]
                cur_hour += 1
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
                    selected_peaks.append(largest_gap_center)
                else:
                    selected_peaks = [12,36,60,84,108,132,156]
                    cur_hour = 0
                    starts = []
                    ends = []
            if not scheduled_hour_successul and len(starts) == 7:
                selected_peaks = [12,36,60,84,108,132,156]
                cur_hour = 0
                starts = []
                ends = []
                
        return starts, ends
    
    def cmp(self, base_main, base_aux, base_allowed, a_main, a_aux, a_allowed,
            b_main, b_aux, b_allowed):
        return base_allowed == True and \
            ( \
              ( \
                base_main < a_main or a_allowed == False \
                or (base_main == a_main and base_aux >= a_aux) \
              ) \
              and \
              ( \
                base_main < b_main or b_allowed == False \
                or (base_main == b_main and base_aux >= b_aux) \
              )\
            )