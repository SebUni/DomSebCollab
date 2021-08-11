# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 14:00:30 2021

@author: S3739258
"""

import os
import fiona

import matplotlib.pyplot as plt
import matplotlib.patches

from console_output import ConsoleOutput
from cast import Cast
from csv_helper import CSVHelper

# constants
SINGLE_RUN = ["charge_received_time_series", "charger_utilisation_time_series",
              "location_time_series"]
D1_SWEEP = ["sweep_data"]
D2_SWEEP = ["avg_cost", "avg_cost_apartment", "avg_cost_house_no_pv",
            "avg_cost_house_pv", "charge_emergency", "charge_grid",
            "charge_held_back", "charge_pv", "charge_work", "utilisation"]
PATH = "results"

MY_DPI = 96

# ### comparison parameters
# general
nbr_of_agents = 1200
# run A
season_a = "1"
model_a = 1
addendum_a = ""

# run B
season_b = "1"
model_b = 6
addendum_b = ""

# use moving avg? (0 is no)
half_avg_over = 10

def file_name(model, nbr_of_agents, season, identifier, addendum, ending):
    if addendum == "":
        return "model_{}_nbr_agents_{}_season_{}_{}{}".format(model,
                                    nbr_of_agents, season, identifier, ending)
    else:
        return "model_{}_nbr_agents_{}_season_{}_{}_{}{}".format(model,
                        nbr_of_agents, season, addendum, identifier, ending)

def path_file_name(model, nbr_of_agents, season, identifier, addendum,
                   ending):
    return "{}/{}".format(PATH, file_name(model, nbr_of_agents, season,
                                         identifier, addendum, ending))

def moving_avg(lst):
    lst_avg = []
    for it, value in enumerate(lst):
        lst_avg.append(0)
        for it_correct in range(- half_avg_over, half_avg_over + 1):
            lst_avg[-1] += lst[(it + it_correct) % len(lst)]
        lst_avg[-1] /= len(range(- half_avg_over, half_avg_over + 1))
    return lst_avg

def determine_missing_files(identifiers):
    missing_files = dict()
    for identifier in identifiers:
        for run in range(2):
            if not os.path.isfile(path_file_name(models[run], nbr_of_agents,
                            seasons[run], identifier, addendums[run], ".csv")):
                if identifier not in missing_files:
                    missing_files[identifier] = [run]
                else:
                    missing_files[identifier].append(run)
    nbr_missing_files \
        = len([item for sublist in missing_files.values() for item in sublist])
    return nbr_missing_files, missing_files

def subtract_2d_matrix(matricies):
    matrix_diff = []
    for col in range(len(next(iter(matricies)))):
        matrix_diff.append(list())
        for row in range(len(next(iter(next(iter(matricies)))))):
            diff = matricies[0][col][row] - matricies[1][col][row]
            matrix_diff[-1].append(diff)
    return matrix_diff

def load_locations():
    """
    Reads information on individual suburbs from locations.csv.
    """
    cast = Cast("Location")
    sa_level = 3
    locations_SA3 = dict()
    csv_helper = CSVHelper("data/SA" + str(sa_level),"locations.csv")
    for row in csv_helper.data:
        uid = cast.to_positive_int(row[0], "Uid")
        name = row[1]
        locations_SA3[uid] = name
    sa_level = 4
    locations_SA4 = dict()
    csv_helper = CSVHelper("data/SA" + str(sa_level),"locations.csv")
    for row in csv_helper.data:
        uid = cast.to_positive_int(row[0], "Uid")
        name = row[1]
        locations_SA4[uid] = name
    return locations_SA3, locations_SA4

def time_axis_labels(time_steps):
    max_labels = 22
    total_hours = len(time_steps) // 12
    hour_lbl_step = total_hours // max_labels
    if hour_lbl_step > 24:
        hour_lbl_step = 24
    while 24 % hour_lbl_step != 0:
        hour_lbl_step += 1
    lbl_time_steps, lbl_hour_steps = [], []
    for time_step in time_steps:
        if time_step % 12 == 0:
            hour = time_step // 60 % 24
            if hour % hour_lbl_step == 0:
                lbl_time_steps.append(time_step)
                lbl_hour_steps.append(hour)
    
    return lbl_time_steps, lbl_hour_steps

def get_color(value, min_value, max_value):
    _max = max(abs(min_value), max_value)
    rel_value = value / _max
    if rel_value <= 0:
        return [1+rel_value,1+rel_value,1]
    else:
        return [1,1-rel_value,1-rel_value]
            
def read_data(relative_path, file_name):
    cast = Cast("difference_tool")
    csv_helper = CSVHelper(relative_path, file_name, skip_header=False)
    firstRowRead = False
    first_row, front_col, data = [], [], []
    for row in csv_helper.data:
        if not firstRowRead:
            first_row = [cell for cell in row]
            firstRowRead = True
        else:
            front_col.append(row[0])
            data.append([cast.to_float(cell, "data_cell") for cell in row[1:]])
    return first_row, front_col, data

def write_to_csv(pf_name, header, front_col, data):
    with open(pf_name, 'w') as f:
        print(header, file=f)
        for row_it, front_cell in enumerate(front_col):
            line = str(front_cell)
            for cell in data[row_it]:
                line += "," + str(cell)
            print(line, file=f)
            
def decide_what_to_do(co, identifiers, title, analyses_function):
    nbr_missing_files, missing_files \
        = determine_missing_files(identifiers)
    if nbr_missing_files == 0:
        handle_diff_comparision(identifiers, analyses_function)
        co.t_print("Analysed {} for differences!".format(title))
    elif nbr_missing_files != len(identifiers) * 2: # 2 is amount of runs comp.
        co.t_print("Files missing to analyse {}:".format(title))
        for _identifier, _run in missing_files.items():
            str_runs = "A + B"
            if _run == [0]: str_runs = "A"
            elif _run == [1]: str_runs = "B"
            co.t_print("{} misses run(s): {}".format(_identifier, str_runs))
    else:
        # no files to average for Single-Run-Session
        return False
    return True

def handle_diff_comparision(identifiers, analyses_function):
    data_diff = dict()
    front_col = dict()
    first_row = dict()
    for identifier in identifiers:
        first_row[identifier], front_col[identifier] = [], []
        data = []
        header = ""
        for run in range(2):
            fname = file_name(models[run], nbr_of_agents, seasons[run],
                              identifier, addendums[run], ".csv")
            first_row[identifier], front_col[identifier], tmp_data \
                = read_data(PATH, fname)
            header = ""
            for cell in first_row[identifier]:
                if header != "": header += ","
                header += cell
            data.append(tmp_data)
        data_diff[identifier] = subtract_2d_matrix(data)
        frmt = lambda lst : str(lst[0]) + "-" + str(lst[1])
        pf_name = path_file_name(frmt(models), nbr_of_agents,
                                 frmt(seasons), "diff_" + str(identifier),
                                 frmt(addendums), ".csv")
        write_to_csv(pf_name, header, front_col[identifier],
                     data_diff[identifier])
    analyses_function(identifiers, first_row, front_col, data_diff)

def analyse_single_run_diff(identifiers, first_row, front_col, data_diff):
    cast = Cast("Analysis")
    frmt = lambda lst : str(lst[0]) + "-" + str(lst[1])
    time_steps = [cast.to_int(row, "front_row_cell")\
                  for row in front_col[identifiers[0]]]
    lbl_time_steps, lbl_hour_steps = time_axis_labels(time_steps)
    # charge delivered by source // identifiers[0]
    pf_name = path_file_name(frmt(models), nbr_of_agents, frmt(seasons),
                             "diff_" + identifiers[0], frmt(addendums), ".png")
    fig, ax = plt.subplots()
    for data_set_it, title in enumerate(first_row[identifiers[0]][1:]):
        ax.plot(time_steps,
                moving_avg([row[data_set_it] \
                            for row in data_diff[identifiers[0]]]),
                label=title)
    ax.set(xlabel="time in hours", ylabel="kWh / 5 min")
    plt.xticks(lbl_time_steps, lbl_hour_steps)
    plt.grid(axis='x', color='0.95')
    plt.legend()
    plt.show()
    fig.savefig(pf_name, bbox_inches='tight', pad_inches=0.1)
    # charge utilisation // identifiers[1]
    pf_name = path_file_name(frmt(models), nbr_of_agents, frmt(seasons),
                             "diff_" + identifiers[1], frmt(addendums), ".png")
    fig, ax = plt.subplots()
    ax.plot(time_steps, moving_avg([row[0]*100 \
                                    for row in data_diff[identifiers[1]]]))
    ax.set(xlabel="time in hours", ylabel="Charger utilisation in %")
    plt.xticks(lbl_time_steps, lbl_hour_steps)
    plt.grid(axis='x', color='0.95')
    plt.show()
    fig.savefig(pf_name, bbox_inches='tight', pad_inches=0.1)
    # charge injection / withdrawl at location // identifiers[2]
    # get location codes and titles and iterators to find right data_diff entry
    locations_SA3, locations_SA4 = load_locations()
    location_codes = dict()
    for it, location_uid_str in enumerate(first_row[identifiers[2]][1:]):
        SA4_code = cast.to_int(location_uid_str[:3], "location code")
        SA3_code = cast.to_int(location_uid_str, "location code")
        if SA4_code not in location_codes:
            location_codes[SA4_code] = []
        location_codes[SA4_code].append((SA3_code, it))
    # calc data
    SA_data_ts = dict()
    SA3_total = dict()
    SA4_avg = dict()
    for SA4_code, SA3_codes in location_codes.items():
        SA_data_ts[SA4_code] = dict()
        SA4_avg[SA4_code] = []
        for SA3_code, SA3_it in SA3_codes:
            SA_data_ts[SA4_code][SA3_code] \
                =moving_avg([row[SA3_it] for row in data_diff[identifiers[2]]])
            for sub_it, entry in enumerate(SA_data_ts[SA4_code][SA3_code]):
                if len(SA4_avg[SA4_code]) == sub_it:
                    SA4_avg[SA4_code].append(0)
                SA4_avg[SA4_code][sub_it] += entry
            SA3_total[SA3_code] = sum(SA_data_ts[SA4_code][SA3_code])
        SA4_avg[SA4_code] = [entry/len(location_codes[SA4_code])\
                             for entry in SA4_avg[SA4_code]]
    # plot data - temporal
    pf_name = path_file_name(frmt(models), nbr_of_agents, frmt(seasons),
                             "diff_temporal" + identifiers[2], frmt(addendums),
                             ".png")
    fig, axs = plt.subplots(3,3)
    fig.tight_layout(pad=0.4, w_pad=-1, h_pad=0)
    fig.set_size_inches(1920 / MY_DPI, 1080 / MY_DPI)
    location_codes_key_it = iter(location_codes.keys())
    for row_it in range(3):
        for col_it in range(3):
            SA4_code = next(location_codes_key_it)
            SA4_title = locations_SA4[SA4_code]
            axs[col_it, row_it].set_title(SA4_title)
            for SA3_code, SA3_it in location_codes[SA4_code]:
                SA3_data = SA_data_ts[SA4_code][SA3_code]
                SA3_title = locations_SA3[SA3_code]
                axs[col_it, row_it].plot(time_steps, SA3_data, label=SA3_title)         
            axs[col_it, row_it].plot(time_steps, SA4_avg[SA4_code], 'k--',
                                     label="avg")
            axs[col_it, row_it].set_xticks(lbl_time_steps)
            axs[col_it, row_it].set_xticklabels(lbl_hour_steps)
            axs[col_it, row_it].set(xlabel="time in hours",
                                    ylabel="kWh / 5 min")
            axs[col_it, row_it].grid(color='lightgray', linestyle='-',
                                     linewidth=1)
            axs[col_it, row_it].legend()
            
    # plt.title("Diff - Locational injections / withdraws")
    plt.show()
    fig.savefig(pf_name, bbox_inches='tight', pad_inches=0.1, dpi=MY_DPI)
    # plot data - geographic
    # parameters to retrieve area border gps data
    pf_name = path_file_name(frmt(models), nbr_of_agents, frmt(seasons),
                             "diff_geo" + identifiers[2], frmt(addendums),
                             ".png")
    SA4_regions_to_include = [206,207,208,209,210,211,212,213,214]
    export_SA_level = 3
    _layer = "Statistical_Area_Level_" + str(export_SA_level) + "_2016"
    _code = None
    if 3 <= export_SA_level <= 4:
        _code = "SA" + str(export_SA_level) + "_CODE_2016"
    elif export_SA_level == 2:
        _code = "SA" + str(export_SA_level) + "_MAINCODE_2016"
    elif export_SA_level == 1:
        raise RuntimeError("SA code not implemented!")
    else:
        raise RuntimeError("Ill defined SA code!")
    # extract data from model
    min_charge_delivered = 0
    max_charge_delivered = 0
    for charge_delivered in SA3_total.values():
        min_charge_delivered = min(min_charge_delivered, charge_delivered)
        max_charge_delivered = max(max_charge_delivered, charge_delivered)
    
    # Check if retreived data fits map data
    # data retrieved from
    # https://data.gov.au/data/dataset/asgs-2016-edition-boundaries
    _file_name = "asgs2016absstructuresmainstructureandgccsa.gpkg"
    _file_path \
        = "data\\generators\\locations\\sa_code, sa_names, cooridnates\\"
    
    # plot data
    fig = plt.figure(figsize=(1080 / MY_DPI, 1080 / MY_DPI))
    ax = fig.add_subplot(111)
    with fiona.open(_file_path + _file_name, layer=_layer) as layer:
        nbr_of_drawn_sas = 0
        for export_level_region in layer:
            elr = export_level_region
            is_in_selected_SA4_region = False
            for SA4_region in SA4_regions_to_include:
                if str(SA4_region) \
                    == elr['properties'][_code][:len(str(SA4_region))]:
                    is_in_selected_SA4_region = True
                    break
            if is_in_selected_SA4_region:
                elr_code = int(elr['properties'][_code])
                charge_value = SA3_total[elr_code]
                color_data = get_color(charge_value, min_charge_delivered,
                                       max_charge_delivered)
                for patch_data in elr['geometry']['coordinates']:
                    x = [data[0] for data in patch_data[0]]
                    y = [data[1] for data in patch_data[0]]
                    p = matplotlib.patches.Polygon(patch_data[0],
                                                   facecolor=color_data)
                    ax.add_patch(p)
                    ax.plot(x, y, color='black', linewidth=1)    
                nbr_of_drawn_sas += 1
    
    ax.margins(0.1)
    ax.axis('off')
    plt.show()
    fig.savefig(pf_name, bbox_inches='tight', pad_inches=0.1, dpi=MY_DPI)

def analyse_1d_sweep_diff(identifiers, first_row, front_col, data_diff):
    co.t_print("1-Dimensional-Sweep comparison not implement yet!")

def analyse_2d_sweep_diff(identifiers, first_row, front_col, data_diff):
    co.t_print("2-Dimensional-Sweep comparison not implement yet!")
            
# formated output
co = ConsoleOutput()

seasons = (season_a, season_b)
models = (model_a, model_b)
addendums = (addendum_a, addendum_b)

no_files_found = True

# analyse Single-Run-Session
files_found = decide_what_to_do(co, SINGLE_RUN, "Single-Run-Session",
                                analyse_single_run_diff)
if files_found: no_files_found = False

# analyse 1-Dimensional-Sweep
files_found = decide_what_to_do(co, D1_SWEEP, "1-Dimensional-Sweep",
                                analyse_1d_sweep_diff)
if files_found: no_files_found = False

# analyse 2-Dimensional-Sweep
files_found = decide_what_to_do(co, D2_SWEEP, "2-Dimensional-Sweep",
                                analyse_2d_sweep_diff)
if files_found: no_files_found = False

if no_files_found:
    co.t_print("No matching set of files found!")