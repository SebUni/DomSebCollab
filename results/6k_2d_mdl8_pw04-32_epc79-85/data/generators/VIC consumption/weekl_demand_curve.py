# -*- coding: utf-8 -*-
"""
Created on Sat Oct  2 16:28:18 2021

@author: S3739258
"""

from cast import Cast
from csv_helper import CSVHelper

file_raw = "PRICE_AND_DEMAND_2020*_VIC1.csv"

months = [f'{i:02d}' for i in range(1, 13)]

demands = []

for month in months:
    file_name = file_raw.replace("*", month)
    cast = Cast("months demand")
    csv_helper = CSVHelper("", file_name, skip_header=True)
    for row in csv_helper.data:
        demands.append(cast.to_float(row[2], "demand"))

week_half_hour_demands = [0 for i in range(0,7*24*2)]

count_days = [0 for i in range(0,7)]

cur_time_step = 2 * 24 * 2 # first day of the year was a wednesday
for demand in demands:
    for i in range(0,7):
        if i*24*2 == cur_time_step:
            count_days[i] += 1
    week_half_hour_demands[cur_time_step] += demand
    cur_time_step = (cur_time_step + 1) % (7*24*2)

for it in range(len(week_half_hour_demands)):
    for i in range(0,7):
        if i*24*2 <= it < (i+1)*24*2:
            week_half_hour_demands[it] /= count_days[i]
            print(week_half_hour_demands[it])
    