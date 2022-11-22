# -*- coding: utf-8 -*-
"""
Created on Tue Jan 26 10:53:52 2021

@author: S3739258
"""

import csv
from csv_helper import CSVHelper
from cast import Cast

SA4_regions_to_include = [206,207,208,209,210,211,212,213,214]
# select either Statistical Area 3 and 4
SA_LEVEL = 4
# do not touch
SA_column = 1 if SA_LEVEL == 3 else 3

# relevant for climate zone 6
# taken from "ENERGY CONSUMPTION BENCHMARKS ELECTRICITY AND GASFOR RESIDENTIAL
# CUSTOMERS" by Acil Allen page 23
have_pool = 0.15
# relevant for climate zone 4
# taken from "ENERGY CONSUMPTION BENCHMARKS ELECTRICITY AND GASFOR RESIDENTIAL
# CUSTOMERS" by Acil Allen page 24
have_gas = 0.44
# relevant for climate zone 7
# taken from "ENERGY CONSUMPTION BENCHMARKS ELECTRICITY AND GASFOR RESIDENTIAL
# CUSTOMERS" by Acil Allen page 23
have_underfloor_heating = 0.06

days_in_spring = 31+30+31
days_in_summer = 31+28+31
days_in_autumn = 30+31+30
days_in_winter = 31+31+30

hours_per_day = 24

# calculate seasonal consumption for statistical area
cast = Cast("Climate Zone Mapping")
csv_helper = CSVHelper("","climate_zone_mapping_victoria.csv")
climate_zone_mapping = dict()
for row in csv_helper.data:
    postal_area = cast.to_positive_int(row[0], "postal_area")
    climate_zone = cast.to_positive_int(row[1], "climate_zone")
    climate_zone_mapping[postal_area] = climate_zone

cast = Cast("Mesh Block to Post Area")
csv_helper = CSVHelper("","mesh_block_to_postal_area.csv")
mesh_block_to_postal_area = dict()
for row in csv_helper.data:
    mesh_block = cast.to_positive_int(row[0], "mesh_block")
    postal_area = cast.to_positive_int(row[1], "postal_area")
    mesh_block_to_postal_area[mesh_block] = postal_area

cast = Cast("Mesh Block to Statistical Area")
csv_helper = CSVHelper("","mesh_block_to_statistical_area.csv")
mesh_block_to_stat_area = dict()
for row in csv_helper.data:
    mesh_block = cast.to_positive_int(row[0], "mesh_block")
    sa4_lvl = cast.to_positive_int(row[3], "sa4 level")
    if sa4_lvl not in SA4_regions_to_include: continue
    statictical_area = cast.to_positive_int(row[SA_column], "statictical_area")
    mesh_block_to_stat_area[mesh_block] = statictical_area

cast = Cast("Dwellings per Postal Area")
csv_helper = CSVHelper("","dwellings_in_postal_area.csv")
dwellings_in_postal_area = dict()
for row in csv_helper.data:
    postal_area = cast.to_positive_int(row[0], "postal_area")
    nbr_of_dwellings = cast.to_positive_int(row[1], "nbr_of_dwellings")
    dwellings_in_postal_area[postal_area] = nbr_of_dwellings

cast = Cast("Seasonal Consumption Climate Zone 4 no Gas")
csv_helper = CSVHelper("","seasonal_consumption_climate_zone_4_no_gas.csv")
sccz4_no_gas = dict()
for row in csv_helper.data:
    household_size = cast.to_positive_int(row[0], "household_size")
    cons_spring = cast.to_positive_float(row[1], "cons_spring")
    cons_summer = cast.to_positive_float(row[2], "cons_summer")
    cons_autumn = cast.to_positive_float(row[3], "cons_autumn")
    cons_winter = cast.to_positive_float(row[4], "cons_winter")
    sccz4_no_gas[household_size] = [cons_spring, cons_summer,
                                    cons_autumn, cons_winter]

cast = Cast("Seasonal Consumption Climate Zone 4 with Gas")
csv_helper = CSVHelper("","seasonal_consumption_climate_zone_4_with_gas.csv")
sccz4_with_gas = dict()
for row in csv_helper.data:
    household_size = cast.to_positive_int(row[0], "household_size")
    cons_spring = cast.to_positive_float(row[1], "cons_spring")
    cons_summer = cast.to_positive_float(row[2], "cons_summer")
    cons_autumn = cast.to_positive_float(row[3], "cons_autumn")
    cons_winter = cast.to_positive_float(row[4], "cons_winter")
    sccz4_with_gas[household_size] = [cons_spring, cons_summer,
                                      cons_autumn, cons_winter]

cast = Cast("Seasonal Consumption Climate Zone 6 no Pool")
csv_helper = CSVHelper("","seasonal_consumption_climate_zone_6_no_pool.csv")
sccz6_no_pool = dict()
for row in csv_helper.data:
    household_size = cast.to_positive_int(row[0], "household_size")
    cons_spring = cast.to_positive_float(row[1], "cons_spring")
    cons_summer = cast.to_positive_float(row[2], "cons_summer")
    cons_autumn = cast.to_positive_float(row[3], "cons_autumn")
    cons_winter = cast.to_positive_float(row[4], "cons_winter")
    sccz6_no_pool[household_size] = [cons_spring, cons_summer,
                                     cons_autumn, cons_winter]
    
cast = Cast("Seasonal Consumption Climate Zone 6 with Pool")
csv_helper = CSVHelper("","seasonal_consumption_climate_zone_6_with_pool.csv")
sccz6_with_pool = dict()
for row in csv_helper.data:
    household_size = cast.to_positive_int(row[0], "household_size")
    cons_spring = cast.to_positive_float(row[1], "cons_spring")
    cons_summer = cast.to_positive_float(row[2], "cons_summer")
    cons_autumn = cast.to_positive_float(row[3], "cons_autumn")
    cons_winter = cast.to_positive_float(row[4], "cons_winter")
    sccz6_with_pool[household_size] = [cons_spring, cons_summer,
                                       cons_autumn, cons_winter]

cast = Cast("Seasonal Consumption Climate Zone 7 no Underfloor Heating")
csv_helper = CSVHelper("","seasonal_consumption_climate_zone_7_no_underfloor_heating.csv")
sccz7_no_underfloor_heating = dict()
for row in csv_helper.data:
    household_size = cast.to_positive_int(row[0], "household_size")
    cons_spring = cast.to_positive_float(row[1], "cons_spring")
    cons_summer = cast.to_positive_float(row[2], "cons_summer")
    cons_autumn = cast.to_positive_float(row[3], "cons_autumn")
    cons_winter = cast.to_positive_float(row[4], "cons_winter")
    sccz7_no_underfloor_heating[household_size] = [cons_spring, cons_summer,
                                                   cons_autumn, cons_winter]
    
cast = Cast("Seasonal Consumption Climate Zone 7 with Underfloor Heating")
csv_helper = CSVHelper("","seasonal_consumption_climate_zone_7_with_underfloor_heating.csv")
sccz7_with_underfloor_heating = dict()
for row in csv_helper.data:
    household_size = cast.to_positive_int(row[0], "household_size")
    cons_spring = cast.to_positive_float(row[1], "cons_spring")
    cons_summer = cast.to_positive_float(row[2], "cons_summer")
    cons_autumn = cast.to_positive_float(row[3], "cons_autumn")
    cons_winter = cast.to_positive_float(row[4], "cons_winter")
    sccz7_with_underfloor_heating[household_size] = [cons_spring, cons_summer,
                                                     cons_autumn, cons_winter]


# assign postal areas to statistical areas
mesh_blocks_in_stat_area = dict()
for mesh_block in mesh_block_to_stat_area.keys():
    statictical_area = mesh_block_to_stat_area[mesh_block]
    if statictical_area not in mesh_blocks_in_stat_area.keys():
        mesh_blocks_in_stat_area[statictical_area] = []
    mesh_blocks_in_stat_area[statictical_area].append(mesh_block)
    
mesh_blocks_in_postal_area = dict()
for mesh_block in mesh_block_to_postal_area.keys():
    postal_area = mesh_block_to_postal_area[mesh_block]
    if postal_area not in mesh_blocks_in_postal_area.keys():
        mesh_blocks_in_postal_area[postal_area] = []
    mesh_blocks_in_postal_area[postal_area].append(mesh_block)
    
postal_areas_in_stat_areas = dict()
for postal_area, mesh_blocks in mesh_blocks_in_postal_area.items():
    # check which statisitcal areas the mesh blocks of a postal area lie in
    occurence_in_stat_area = dict()
    for mesh_block in mesh_blocks:
        if mesh_block not in mesh_block_to_stat_area.keys():
            continue
        stat_area = mesh_block_to_stat_area[mesh_block]
        if stat_area not in occurence_in_stat_area.keys():
            occurence_in_stat_area[stat_area] = 0
        occurence_in_stat_area[stat_area] += 1
    # check which statistical area most mesh block lie in
    highest_mesh_block_count = 0
    most_suitable_stat_area = -1
    for stat_area, count in occurence_in_stat_area.items():
        if count > highest_mesh_block_count:
            most_suitable_stat_area = stat_area
            highest_mesh_block_count = count
    if most_suitable_stat_area == -1: continue
    if most_suitable_stat_area not in postal_areas_in_stat_areas.keys():
        postal_areas_in_stat_areas[most_suitable_stat_area] = []
    postal_areas_in_stat_areas[most_suitable_stat_area].append(postal_area)
        
# combining sucategories for scczs
sccz4 = dict()
for i in sccz4_no_gas.keys():
    sccz4[i] = []
    for j in range(len(sccz4_no_gas[i])):
        value = sccz4_no_gas[i][j] * (1 - have_gas) \
              + sccz4_with_gas[i][j] * have_gas
        sccz4[i].append(value)

sccz6 = dict()
for i in sccz6_no_pool.keys():
    sccz6[i] = []
    for j in range(len(sccz6_no_pool[i])):
        value = sccz6_no_pool[i][j] * (1 - have_pool) \
              + sccz6_with_pool[i][j] * have_pool
        sccz6[i].append(value)

sccz7 = dict()
for i in sccz7_no_underfloor_heating.keys():
    sccz7[i] = []
    for j in range(len(sccz7_no_underfloor_heating[i])):
        value = sccz7_no_underfloor_heating[i][j] * (1 - have_underfloor_heating) \
              + sccz7_with_underfloor_heating[i][j] * have_underfloor_heating
        sccz7[i].append(value)
        
sc = {4 : sccz4, 6 : sccz6, 7 : sccz7}

# assign consumption to statistical areas
consumption_in_stat_area = dict()
# PHH = PersonHousehold
header = "#StatisticalArea," \
         +"1PHHSpring,2PHHSpring,3PHHSpring,4PHHSpring,5PHHSpring," \
         +"1PHHSummer,2PHHSummer,3PHHSummer,4PHHSummer,5PHHSummer," \
         +"1PHHAutumn,2PHHAutumn,3PHHAutumn,4PHHAutumn,5PHHAutumn," \
         +"1PHHWinter,2PHHWinter,3PHHWinter,4PHHWinter,5PHHWinter"
for stat_area, postal_areas in postal_areas_in_stat_areas.items():
    # consumption for 1, 2, 3, 4 or 5 person household hence a list
    consumption = [0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0]
    total_nbr_of_dwellings = 0
    for postal_area in postal_areas:
        climate_zone = climate_zone_mapping[postal_area]
        nbr_of_dwellings = dwellings_in_postal_area[postal_area]
        for nbr_PHH, seasonal_consumptions in sc[climate_zone].items():
            for season_it, seasonal_consumption in enumerate(seasonal_consumptions):
                it = (nbr_PHH-1)+5*season_it
                consumption[it] += seasonal_consumption*nbr_of_dwellings
        total_nbr_of_dwellings += nbr_of_dwellings
    for i in range(len(consumption)):
        if i < 5:
            consumption[i] /= days_in_spring
        if 5 <= i < 10:
            consumption[i] /= days_in_summer
        if 10 <= i < 15:
            consumption[i] /= days_in_autumn
        if 15 <= i:
            consumption[i] /= days_in_winter
        consumption[i] /= hours_per_day
        consumption[i] = round(consumption[i] / total_nbr_of_dwellings, 4)
    consumption_in_stat_area[stat_area] = consumption
        
# save to csv
file_name = "consumption_deviation_statistical_area_" + str(SA_LEVEL) + ".csv"
with open(file_name, mode='w') as employee_file:
    wr = csv.writer(employee_file, delimiter=',',
                                 quotechar='"',
                                 quoting=csv.QUOTE_MINIMAL)
    wr.writerow(header.split(","))
    for stat_area, row in consumption_in_stat_area.items():
        wr.writerow([stat_area] + row)
