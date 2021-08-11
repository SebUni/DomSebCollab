# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 11:00:09 2021

@author: S3739258
"""

import os

from console_output import ConsoleOutput
from cast import Cast
from csv_helper import CSVHelper

def file_name(model, nbr_of_agents, season, identifier):
    return "model_{}_nbr_agents_{}_season_{}_{}.csv".format(model,
                                            nbr_of_agents, season, identifier)

def path_file_name(path, model, nbr_of_agents, season, identifier):
    return "{}/{}".format(path, file_name(model, nbr_of_agents, season,
                                         identifier))

def read_data(relative_path, file_name):
    cast = Cast("average_season")
    csv_helper = CSVHelper(relative_path, file_name, skip_header=False)
    firstRowRead = False
    header = ""
    front_col = []
    data = []
    for row in csv_helper.data:
        if not firstRowRead:
            for cell_it, cell in enumerate(row):
                if cell_it != 0: header += ","
                header += cell
            firstRowRead = True
        else:
            for cell_it, cell in enumerate(row):
                if cell_it == 0:
                    front_col.append(cell)
                    data.append(list())
                else:
                    data[-1].append(cast.to_float(cell, "data_cell"))
    return header, front_col, data

def avg_2d_matrix(matrix):
    matrix_avg = []
    for col in range(len(next(iter(matrix)))):
        matrix_avg.append(list())
        for row in range(len(next(iter(next(iter(matrix)))))):
            avg = sum([season_data[col][row] for season_data in matrix]) \
                / len(matrix)
            matrix_avg[-1].append(avg)
    return matrix_avg
    
def determine_missing_files(identifiers, seasons):
    missing_files = dict()
    for identifier in identifiers:
        for season in seasons:
            if not os.path.isfile(path_file_name(PATH, model, nbr_of_agents,
                                                 season, identifier)):
                if identifier not in missing_files:
                    missing_files[identifier] = [season]
                else:
                    missing_files[identifier].append(season)
    nbr_missing_files \
        = len([item for sublist in missing_files.values() for item in sublist])
    return nbr_missing_files, missing_files

def write_to_csv(pf_name, header, front_col, data):
    with open(pf_name, 'w') as f:
        print(header, file=f)
        for row_it, front_cell in enumerate(front_col):
            line = str(front_cell)
            for cell in data[row_it]:
                line += "," + str(cell)
            print(line, file=f)
            
def handle_averaging_all_identifiers(identifiers):
    for identifier in identifiers:
        header, front_col = "", []
        data = []
        for season in SEASONS:
            fname = file_name(model, nbr_of_agents, season, identifier)
            header, front_col, tmp_data = read_data(PATH, fname)
            data.append(tmp_data)
        data_avg = avg_2d_matrix(data)
        pf_name = path_file_name(PATH, model, nbr_of_agents, "avg", identifier)
        write_to_csv(pf_name, header, front_col, data_avg)
        
def decide_what_to_do(co, identifiers, title, seasons):
    nbr_missing_files, missing_files \
        = determine_missing_files(identifiers, seasons)
    if nbr_missing_files == 0:
        handle_averaging_all_identifiers(identifiers)
        co.t_print("Averaged {}".format(title))
    elif nbr_missing_files != len(identifiers) * len(seasons):
        co.t_print("Files missing to average {}:".format(title))
        for _identifier, _seasons in missing_files.items():
            co.t_print("{} misses seasons: {}".format(_identifier, _seasons))
    else:
        # no files to average for Single-Run-Session
        return False
    return True

# formated output
co = ConsoleOutput()

# constants
SINGLE_RUN = ["charge_received_time_series", "charger_utilisation_time_series",
              "location_time_series"]
D1_SWEEP = ["sweep_data"]
D2_SWEEP = ["avg_cost", "avg_cost_apartment", "avg_cost_house_no_pv",
            "avg_cost_house_pv", "charge_emergency", "charge_grid",
            "charge_held_back", "charge_pv", "charge_work", "utilisation"]
PATH = "results"
SEASONS = [0,1,2,3]

# specify runs to average over
model = 4
nbr_of_agents = 10

no_files_found = True

# Average Single-Run-Session
files_found = decide_what_to_do(co, SINGLE_RUN, "Single-Run-Session", SEASONS)
if files_found: no_files_found = False

# Average 1-Dimensional-Sweep
files_found = decide_what_to_do(co, D1_SWEEP, "1-Dimensional-Sweep", SEASONS)
if files_found: no_files_found = False

# Average 2-Dimensional-Sweep
files_found = decide_what_to_do(co, D2_SWEEP, "2-Dimensional-Sweep", SEASONS)
if files_found: no_files_found = False

if no_files_found:
    co.t_print("No matching set of files found!")