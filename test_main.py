# -*- coding: utf-8 -*-
"""
Created on Mon Jun 28 19:59:59 2021

@author: S3739258
"""

import random
import test_class

def th(hour):
    if hour < 0:
        return hour + 168
    if hour >= 168:
        return hour - 168
    return hour

tc = test_class.TestClass()

worked_hours = []
for i in range(10000):
    worked_hours.append(tc.draw_hours_worked_per_week_at_random())

worked_hours.sort(reverse=True)

tracked_hours = []
for i in range(168):
    tracked_hours.append(0)
    
tc.prepare_schedule_generation()
for i in range(10000):
    hours_worked_per_week = worked_hours[i]
    starts, ends = tc.generate_schedule(hours_worked_per_week)
    for k in range(len(starts)):
        for j in range(starts[k], ends[k]+1):
            tracked_hours[th(j)] += 1

for tracked_hour in tracked_hours:
    print(tracked_hour)