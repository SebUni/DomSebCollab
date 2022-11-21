# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 15:24:17 2021

@author: S3739258
"""

import csv

import numpy
from scipy.stats import norm
from scipy import special
from scipy.optimize import curve_fit

import matplotlib.mlab
import matplotlib.pyplot

from cast import Cast

def scaled_N(x, mu, sig, A):
    return A/(numpy.sqrt(2*numpy.pi)*sig)*numpy.exp(-(x-mu)**2/(2*sig**2))

cast = Cast("Hourly Consumption Data")
data = []
read_header = False
hour_data = dict()
with open("hourly_consumption.csv", newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in reader:
        if read_header == False:
            read_header = True
        else:
            data_point = []
            hour = row[0]
            spring_row = [0, cast.to_positive_float(row[1],"spring_10perc"),
                             cast.to_positive_float(row[2],"spring_50perc"),
                             cast.to_positive_float(row[3],"spring_90perc")]
            summer_row = [0, cast.to_positive_float(row[4],"summer_10perc"),
                             cast.to_positive_float(row[5],"summer_50perc"),
                             cast.to_positive_float(row[6],"summer_90perc")]
            autumn_row = [0, cast.to_positive_float(row[7],"autumn_10perc"),
                             cast.to_positive_float(row[8],"autumn_50perc"),
                             cast.to_positive_float(row[9],"autumn_90perc")]
            winter_row = [0, cast.to_positive_float(row[10],"winter_10perc"),
                             cast.to_positive_float(row[11],"winter_50perc"),
                             cast.to_positive_float(row[12],"winter_90perc")]
            
            hour_data[hour] = [spring_row, summer_row, autumn_row, winter_row]

y_10perc = norm.pdf(numpy.sqrt(2)*special.erfinv(2*0.1-1))
y_50perc = norm.pdf(0.0)
y_90perc = y_10perc
y = [0, y_10perc, y_50perc, y_90perc]

hour_fit = dict()
for hour, hour_data_point in hour_data.items():
    hour_fit[hour] = []
    for season_row in hour_data_point:
        x_10perc = season_row[1]
        x_50perc = season_row[2]
        x_90perc = season_row[3]
        
        init_guess = [(x_90perc - x_50perc) / 2, 1]
        lower_bounds = [0. , 0.]
        upper_bounds = [x_90perc - x_50perc, numpy.inf]
        
        scaled_N_fixed_mu = lambda x, sig, A: scaled_N(x, x_50perc, sig, A)
        mu = x_50perc
        (sig, A), _ = curve_fit(scaled_N_fixed_mu, season_row, y, init_guess,
                                    bounds=(lower_bounds, upper_bounds))
        
        hour_fit[hour].append(mu)
        hour_fit[hour].append(sig)
        hour_fit[hour].append(sig/mu)

file_name = "hourly_consumption_fit.csv"
with open(file_name, mode='w', newline='') as output_file:
    output_file = csv.writer(output_file, delimiter=',', quotechar='"',
                             quoting=csv.QUOTE_NONE)
    header = ["#elapsed_minutes",
              "mu_spring","sig_spring","sig/mu_spring",
              "mu_summer","sig_summer","sig/mu_summer",
              "mu_autumn","sig_autumn","sig/mu_autumn",
              "mu_winter","sig_winter","sig/mu_winter"]
    output_file.writerow(header)
        
    keylist = list(hour_fit.keys())
    #keylist.sort()
    
    x = list(numpy.arange(-2,6.1,0.02))
    for key in keylist:
        output_file.writerow([key] + hour_fit[key])
        
        # mu, sig = hour_fit[key][0], hour_fit[key][1]
        # l_spring = matplotlib.pyplot.plot(x, norm.pdf(x, mu, sig), label='spring')
        # mu, sig = hour_fit[key][2], hour_fit[key][3]
        # l_summer = matplotlib.pyplot.plot(x, norm.pdf(x, mu, sig), label='summer')
        # mu, sig = hour_fit[key][4], hour_fit[key][5]
        # l_autumn = matplotlib.pyplot.plot(x, norm.pdf(x, mu, sig), label='autumn')
        # mu, sig = hour_fit[key][6], hour_fit[key][7]
        # l_winter = matplotlib.pyplot.plot(x, norm.pdf(x, mu, sig), label='winter')
    
        # title_str = "hour = " + str(key)
        # matplotlib.pyplot.title(title_str)
        # matplotlib.pyplot.xlabel('Usage')
        # matplotlib.pyplot.ylabel('Probability')
        # matplotlib.pyplot.grid(True)
        # matplotlib.pyplot.legend()
    
        # matplotlib.pyplot.show()