# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 12:41:43 2021

@author: S3739258

This script takes data aquired from solcast.com and extracts as well as
calculates parameteres used in the charging_model simulation.

As an input the script looks for a file called solcast.csv in the same folder
as the script is located in.

The script allows to specify which rows are extracted from the source file. 
For this functionality please look into section

The script can return:
    
    1) "solar_irradiance.csv" - a file which 
"""

"""
SECTION 0.a: Imports
"""

import sys
import csv

import statistics
from scipy.stats import norm
from scipy import special
import matplotlib.mlab
import matplotlib.pyplot

from scipy.optimize import curve_fit

import numpy

from cast import Cast
               
"""
SECTION 0.b: Function definition

These functions are used to fit the data in SECTION
"""

def func(x, A, mu, sig, y0):
    return (1/(numpy.sqrt(2*numpy.pi))) \
           *(A/sig)*numpy.exp(-((x-mu)*(x-mu)/(2*sig*sig))) + y0
           
def func_po(x, A, mu, sig):
    return (1/(numpy.sqrt(2*numpy.pi))) \
           *(A/sig)*numpy.exp(-((x-mu)*(x-mu)/(2*sig*sig)))

"""
SECTION 0.c: Parameter selection

Currently if slcted_col_names or slcted_col_types are changed the script will
break in SECTION 2 as it is not checked at what position Ghi and AirTemp are
stored.
"""

# select col names
slcted_col_names = ["PeriodStart", "GtiFixedTilt", "AirTemp"]
slcted_col_types = ["date",        "int",          "float"  ]
slcted_cols = []
for item in slcted_col_names:
    slcted_cols.append(-1)
    
remove_char_from_Date = ["-", "T", ":", "Z"]

season_name = {0 : "spring",
               1 : "summer",
               2 : "autumn",
               3 : "winter"}

store_raw_data = False

"""
SECTION 1: Read data from source file 

Data from source file "solcast.csv" is read, columns selected in
slcted_col_names extracted and store in data list.
"""

print("Read data!")

cast = Cast("Solar Irradiance Data")
data = []
read_header = False
with open("solcast.csv", newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in reader:
        if read_header == False:
            for header_col, header_name in enumerate(row):
                for slcted_col, slcted_col_name in enumerate(slcted_col_names):
                    if slcted_col_name == header_name:
                        slcted_cols[slcted_col] = header_col
            all_cols_identified = True
            for slcted_col_it, slcted_col in enumerate(slcted_cols):
                if slcted_col == -1:
                    print("Column with name " \
                          + slcted_col_names[slcted_col_it] \
                          + " could not be found.")
                    all_cols_identified = False
            if all_cols_identified == False:
                sys.exit("Exiting as some columns could not be found!")
            else:
                read_header = True
        else:
            data_point = []
            for it, slcted_col in enumerate(slcted_cols):
                string = row[slcted_col]
                if slcted_col_types[it] == "date":
                    # remove excess characters
                    for char in remove_char_from_Date:
                        string = string.replace(char, '')
                    # remove seconds
                    string = string[:-2]
                    # store
                    data_point.append(string)
                elif slcted_col_types[it] == "int":
                    data_point.append(str(cast.to_int(string,
                                                      slcted_col_names[it])))
                elif slcted_col_types[it] == "float":
                    data_point.append(str(cast.to_float(string,
                                                        slcted_col_names[it])))
                else:
                    sys.exit("Data type '" + slcted_col_types[it] \
                             + "' not implemented.")
            data.append(data_point)
            
"""
SECTION 2: Store unprocessed data
"""

"""
if store_raw_data == True:    
    print("Store raw data!")

    with open('solar_irradiance.csv', mode='w', newline='') as output_file:
        output_file = csv.writer(output_file, delimiter=',', quotechar='"',
                                 quoting=csv.QUOTE_MINIMAL)
        header = []
        for it, slcted_col_name in enumerate(slcted_col_names):
            if it == 0:
                header.append("#" + slcted_col_name)
            else:
                header.append(slcted_col_name)
            output_file.writerow(header)
    
        for data_point in data:
            output_file.writerow(data_point)
"""

"""
SECTION 3: Annual & seasonal processing.

This section takes the data of all years found in the source file and
reduces them to one year and / or 4 seasons.

For this year / each season the elapsed time in minutes since the start of the
year / season is calculated as a timestamp. For each timestamp, all values 
associated with that timestamp are stored. E.g.: For the season of spring
the the timestamp for the 1st of October at 00:00 PM that is midnight is 0.
Then for 0 all values found at the 1.10.2007 00:00, 1.10.2008 00:00 and so on
are stored.

This section focuses soley on solar irradiation and temperature.

The list for the yearly data are called irradiances and temperatures. The lists
for the seasonal data are all stored in collective lists called
season_irradiances[season] and season_temperatures[season].

Leap days are excluded.
"""

# more detailed processing
get_season = lambda month : ((month + 3) % 12) // 3
get_month_it_in_season = lambda month : (month - 1) % 3
acc_days_season = [[0,31,61],[0,31,59],[0,30,61],[0,31,62]]
acc_days_year = [0,31,59,90,120,151,181,212,243,273,304,334]
days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31]
irradiances = dict()
temperatures = dict()
normed_output = dict()
season_irradiances = [dict(), dict(), dict(), dict()]
season_temperatures = [dict(), dict(), dict(), dict()]
season_normed_outputs = [dict(), dict(), dict(), dict()]
years = []

for data_point in data:
    date = data_point[0]
    year = cast.to_positive_int(date[0:4], "Year")
    if year not in years:
        years.append(year)
    month = cast.to_positive_int(date[4:6], "Month")
    day = cast.to_positive_int(date[6:8], "Day")
    hour = cast.to_positive_int(date[8:10], "Hour")
    minute = cast.to_positive_int(date[10:12], "Minutes")
    irrad = cast.to_positive_int(data_point[1], "Irradiance")
    temp = cast.to_positive_float(data_point[2], "Temperature")
    
    # Zulu time to Australian Eastern Standard Time // UTC -> AEDT
    hour = ( hour + 10 ) % 24
    if hour < 10:
        day = day + 1
        if day > days_in_month[month - 1]:
            day = 1
            month = month + 1
            if month > 12:
                month = 1
                year = year + 1
                
    season = ((month + 2) % 12) // 3
    # exclude leap days
    if month == 2 and day == 29:
        continue
        
    elapsed_minutes_season = acc_days_season[season][get_month_it_in_season(month)] + day - 1
    elapsed_minutes_season = elapsed_minutes_season * 24 + hour
    elapsed_minutes_season = elapsed_minutes_season * 60 + minute
    elapsed_minutes_season = elapsed_minutes_season
    
    elapsed_minutes_year = acc_days_year[month - 1] + day - 1
    elapsed_minutes_year = elapsed_minutes_year * 24 + hour
    elapsed_minutes_year = elapsed_minutes_year * 60 + minute
    elapsed_minutes_year = elapsed_minutes_year
        
    if elapsed_minutes_season not in season_irradiances[season].keys():
        season_irradiances[season][elapsed_minutes_season] = []
        season_temperatures[season][elapsed_minutes_season] = []
        season_normed_outputs[season][elapsed_minutes_season] = []
    season_irradiances[season][elapsed_minutes_season].append(irrad)
    season_temperatures[season][elapsed_minutes_season].append(temp)
    season_normed_outputs[season][elapsed_minutes_season].append( \
                                            irrad * (1 - (temp - 25) / 200))
    
    irradiances[elapsed_minutes_year] = irrad
    temperatures[elapsed_minutes_year] = temp
    normed_output[elapsed_minutes_year] = irrad * (1 - (temp - 25) / 200)
    
"""
SECTION 4: Store seasonal data.
 
Seasonal data processed in secion 3 are stored in files. Data is stored in
"solar_irradiance_<season_string>.csv" and "temperatures_<season_string>.csv".
"""

"""
for cur_season in range(4):
    keylist = list(season_irradiances[cur_season].keys())
    keylist.sort()
    file_name = "solar_irradiance_" + season_name[cur_season] + ".csv"
    with open(file_name, mode='w', newline='') as output_file:
        output_file = csv.writer(output_file, delimiter=',', quotechar='"',
                                 quoting=csv.QUOTE_MINIMAL)
        header = ["#elapsed_minutes"]
        for year in years:
            header.append(str(year))
        output_file.writerow(header)
    
        for key in keylist:
            output_file.writerow([key] + season_irradiances[cur_season][key])
            
    file_name = "temperatures_" + season_name[cur_season] + ".csv"
    with open(file_name, mode='w', newline='') as output_file:
        output_file = csv.writer(output_file, delimiter=',', quotechar='"',
                                 quoting=csv.QUOTE_MINIMAL)
        header = ["#elapsed_minutes"]
        for year in years:
            header.append(str(year))
        output_file.writerow(header)
    
        for key in keylist:
            output_file.writerow([key] + season_temperatures[cur_season][key])
            
    file_name = "nominal_output_" + season_name[cur_season] + ".csv"
    with open(file_name, mode='w', newline='') as output_file:
        output_file = csv.writer(output_file, delimiter=',', quotechar='"',
                                 quoting=csv.QUOTE_MINIMAL)
        header = ["#elapsed_minutes"]
        for year in years:
            header.append(str(year))
        output_file.writerow(header)
    
        for key in keylist:
            output_file.writerow([key] + season_normed_outputs[cur_season][key])
"""

"""
SECTION 5: Approximate solar output for normed PV rooftop installation.
"""

print("Fit data!")

# calc normed output


minutes_per_interval = list(season_irradiances[0].keys())[1] \
                        - list(season_irradiances[0].keys())[0]

intervals_per_day = 24 * 60 // minutes_per_interval
intervals_per_year = intervals_per_day * 365

fit_output = {}
days_plus_minus = 7

for it_interval in range(intervals_per_year):
    elapsed_minutes = it_interval * minutes_per_interval
    fit_output[elapsed_minutes] = []
    it_sub = it_interval
    while(it_sub < len(data)):
        for it_day in range(-days_plus_minus, days_plus_minus + 1):
            it_slct = it_sub + it_day * intervals_per_day
            if 0 <= it_slct < len(normed_output):
                it_slct_minutes = it_slct * minutes_per_interval
                fit_output[elapsed_minutes].append(normed_output[it_slct_minutes])
        it_sub = it_sub + intervals_per_year

fit_output_data = dict()
it_term, it_R2, R2avg = 0, 0, 0

for elapsed_minutes, outputs in fit_output.items():
    max_output = max(outputs)

    avg = statistics.mean(fit_output[elapsed_minutes])
    std_dev = statistics.stdev(fit_output[elapsed_minutes])

    # the histogram of the data
    n, bins \
        = numpy.histogram(fit_output[elapsed_minutes], bins=30, density=True)
    
    x = []
    for it in range(len(bins)-1):
        x.append((bins[it+1]+bins[it])/2)
    
    init_guess = [1, max_output, max_output / 50, 0]
    lower_bounds = [0., max_output * 0.8 , 0., 0.]
    upper_bounds = [numpy.inf, max_output + .1, max_output / 6 + .1, numpy.inf]
    fit_successful = True
    
    A, mu, sig, y0 = 0, 0, 0, 0
    A_po, mu_po, sig_po = 0.0, 0.0, 0.0
    surf_po, surf_co = 0.0, 0.0
    y_co = 0
    R2 = 0
    
    try:
        (A, mu, sig, y0), pcov \
            = curve_fit(func, x, n, init_guess,
                        bounds=(lower_bounds, upper_bounds))
    except:
        print("Needs manuel calculation")
        print("Elapsed minutes: " + str(elapsed_minutes))
        print("x: " + str(x))
        print("y: " + str(n))
        fit_successful = False
    
    if fit_successful:
        # border between gauss fit and constant fit
        x_border = mu - 2 * sig
        
        # peak only (po) and constant only (co) fit
        x_po, n_po = [], []
        y_sum = 0
        y_count = 0
        for it, x_slct in enumerate(x):
            if x_slct >= x_border:
                x_po.append(x_slct)
                n_po.append(n[it])
            else:
                y_sum = y_sum + n[it]
                y_count = y_count + 1
        
        A_po, mu_po, sig_po = 0.0, 0.0, 0.0
        surf_po, surf_co = 0.0, 1.0
        
        y_co = y_sum / y_count
        
        if len(n_po) != 0:
            init_guess_po = [A, mu, sig]
            try:
                (A_po, mu_po, sig_po), pcov_po \
                    = curve_fit(func_po, x_po, n_po, init_guess_po,
                                bounds=(lower_bounds[0:-1], upper_bounds[0:-1]))
            except:
                max_normal_dist = func(mu, A, mu, sig, 0)
                A_po = (y0 + max_normal_dist) / max_normal_dist
                mu_po, sig_po = mu, sig
            
            # surface covered when only peak is fitted
            surf_po = A_po * .5 \
                  * (special.erf((max_output - mu_po)/(numpy.sqrt(2) * sig_po)) \
                     - special.erf((x_border - mu_po)/(numpy.sqrt(2) * sig_po)))
            
            #surface when only constant is fitted
            surf_co = y_co * x_border
            
            residuals = []
            if surf_po > 1:
                surf_po = 1
                surf_co = 0
            if len(n_po) != 1:
                if surf_po <= surf_co:
                    residuals = n_po- numpy.array([y_co for i in range(len(x_po))])
                else:
                    residuals = n_po- func_po(x_po, *(A_po, mu_po, sig_po))
                rss = numpy.sum(residuals**2)
                rss_tot = numpy.sum((n_po-numpy.mean(n_po))**2)
                if rss_tot != 0:
                    R2 = 1 - (rss / rss_tot)
                    it_R2 += 1
                    R2avg += R2 if it_R2 == 1 else (R2 - R2avg) / it_R2
                else:
                    R2 = 0
            else:
                R2 = -1

    
    fit_output_data[elapsed_minutes] = [int(max_output), int(x_border),
                                        round(A, 3), int(mu), round(sig, 2),
                                        round(y0, 7),
                                        round(A_po, 3), int(mu_po),
                                        round(sig_po, 2), round(y_co, 7),
                                        round(surf_po, 2), round(surf_co, 2),
                                        int(avg), int(std_dev), round(R2,2)]        
    it_term += 1
    if it_term % (24 * 12 * 7) == 0:
        print ("It: {}, R2avg: {}".format(it_term // (24 * 12 * 7), R2avg))
    
    """
    Visual output for fit parameters. Currently lacking source data histogram.
    """
    
    # add a 'best fit' line
    # x_bf, y_bf, y_co_bf = [], [], []
    # x_po_pf, y_po_bf = [], []
    # nbr_of_steps = 200
    # step = max_output / nbr_of_steps
    # upper_limit = max_output + step
    # if upper_limit != 0:
    #     for x_slct in numpy.arange(0, upper_limit, step):
    #         x_bf.append(x_slct)
    #         y_bf.append(func(x_slct, A, mu, sig, y0))
    #         y_co_bf.append(y_co)
    
    #     step = (max_output - x_border) / nbr_of_steps
    #     upper_limit = max_output + step
    #     for x_slct in numpy.arange(x_border, upper_limit, step):
    #         x_po_pf.append(x_slct)
    #         y_po_bf.append(func_po(x_slct, A_po, mu_po, sig_po))
        
    #     l_all = matplotlib.pyplot.plot(x_bf, y_bf, 'r--', linewidth=2)
    #     l_po = matplotlib.pyplot.plot(x_po_pf, y_po_bf, 'r--', linewidth=2)
    #     l_co = matplotlib.pyplot.plot(x_bf, y_co_bf, 'r--', linewidth=2)
    
    # title_str = "surf_po = " + str(round(surf_po, 2)) \
    #     + " || surf_co = " + str(round(surf_co, 2)) 
    # matplotlib.pyplot.title(title_str)
    # matplotlib.pyplot.xlabel('Smarts')
    # matplotlib.pyplot.ylabel('Probability')
    # matplotlib.pyplot.grid(True)
    
    # matplotlib.pyplot.show()
    
    # it_term = it_term + 1
    # if it_term == 24*12:
    #     sys.exit("Lulu")

"""
SECTION 7: Store approximation parameters for normed PV rooftop installation.
"""

file_name = "normed_rooftop_pv_output_fit_parameters_with_R2.csv"
with open(file_name, mode='w', newline='') as output_file:
    output_file = csv.writer(output_file, delimiter=',', quotechar='"',
                             quoting=csv.QUOTE_NONE)
    header = ["#elapsed_minutes","max_output","x_border","A","mu","sig","y0",
              "A_po","mu_po","sig_po","y_co","surf_po","surf_co","avg",
              "std_dev","R2"]
    output_file.writerow(header)
        
    keylist = list(fit_output_data.keys())
    keylist.sort()
    
    for key in keylist:
        key_time_zone_conv = (key + 10 * 60) % (365 * 24 * 60)
        output_file.writerow([key] + fit_output_data[key_time_zone_conv])