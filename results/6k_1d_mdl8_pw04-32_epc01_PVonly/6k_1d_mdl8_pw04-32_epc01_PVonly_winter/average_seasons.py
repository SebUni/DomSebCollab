# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 11:00:09 2021

@author: S3739258
"""

import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches
from mpl_toolkits.axes_grid1 import make_axes_locatable

from console_output import ConsoleOutput
from cast import Cast
from csv_helper import CSVHelper

def file_name(model, nbr_of_agents, season, identifier, ending):
    return "model_{}_nbr_agents_{}_season_{}_{}.{}".format(model,
                                    nbr_of_agents, season, identifier, ending)

def path_file_name(path, model, nbr_of_agents, season, identifier, ending):
    return "{}/{}".format(path, file_name(model, nbr_of_agents, season,
                                         identifier, ending))

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
    
def determine_missing_files(identifiers, seasons, model, nbr_of_agents):
    missing_files = dict()
    for identifier in identifiers:
        for season in seasons:
            if not os.path.isfile(path_file_name(AS_PATH, model, nbr_of_agents,
                                                 season, identifier, "csv")):
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
            
def handle_averaging_all_identifiers(identifiers, sweep_dimension, model,
                                     nbr_of_agents):
    for identifier in identifiers:
        header, front_col = "", []
        data = []
        for season in AS_SEASONS:
            fname = file_name(model, nbr_of_agents, season, identifier, "csv")
            header, front_col, tmp_data = read_data(AS_PATH, fname)
            data.append(tmp_data)
        data_avg = avg_2d_matrix(data)
        pf_name_csv = path_file_name(AS_PATH, model, nbr_of_agents, "avg",
                                     identifier, "csv")
        write_to_csv(pf_name_csv, header, front_col, data_avg)
        if sweep_dimension == 1:
            plot_1D_sweep_results(header, front_col, data_avg, model,
                                  nbr_of_agents)
        if sweep_dimension == 2:
            pf_name_png = path_file_name(AS_PATH, model, nbr_of_agents, "avg",
                                         identifier, "png")
            plot_2D_sweep_results(identifier, header, front_col, data_avg,
                                  pf_name_png)
            
def plot_1D_sweep_results(header, front_col, data, model, nbr_of_agents):
    cast = Cast("average_season")
    # assign data
    data_dict = dict()
    for header_it, header_element in enumerate(header.split(",")[1:]):
        data_dict[header_element] = [row[header_it] for row in data]
    # single parameter scan
    x_data = [cast.to_float(front_col_element, "front col element")
               for front_col_element in front_col]
    x_label = header.split(',')[0]
    # charge delivered by source
    pfname = path_file_name(AS_PATH, model, nbr_of_agents, "avg",
                            "charge_delivered_avg", "png")
    fig, ax = plt.subplots()
    ax.plot(x_data, data_dict["charge_pv"], label="charge_pv")
    ax.plot(x_data, data_dict["charge_work"], label="charge_work")
    ax.plot(x_data, data_dict["charge_grid"], label="charge_grid")
    ax.plot(x_data, data_dict["charge_emergency"], label="charge_emergency")
    ax.plot(x_data, data_dict["charge_held_back"], label="charge_held_back")
    ax.set(xlabel=x_label, ylabel="kWh / 5 min")
    plt.title("Charge delivered by source")
    plt.legend()
    plt.show()
    fig.savefig(pfname, bbox_inches='tight', pad_inches=0.1)
    # average charger utilisation
    pfname = path_file_name(AS_PATH, model, nbr_of_agents, "avg",
                            "avg_charger_utilisation", "png")
    fig, ax = plt.subplots()
    ax.plot(x_data, data_dict["utilisation"])
    ax.set(xlabel=x_label, ylabel="utilisation in %")
    plt.title("Average charger utilisation")
    plt.show()
    fig.savefig(pfname, bbox_inches='tight', pad_inches=0.1)
    # total revenue
    pfname = path_file_name(AS_PATH, model, nbr_of_agents, "avg",
                            "total_revenue", "png")
    fig, ax = plt.subplots()
    ax.plot(x_data, data_dict["total_revenue"])
    ax.set(xlabel=x_label, ylabel="Total Revenue in $")
    plt.title("Total Revenue")
    plt.show()
    fig.savefig(pfname, bbox_inches='tight', pad_inches=0.1)
    # revenue per charger
    fname = file_name(model, nbr_of_agents, "avg", "revenue_per_charger",
                      "png")
    fig, ax = plt.subplots()
    ax.plot(x_data, data_dict["revenue_per_charger"])
    ax.set(xlabel=x_label, ylabel="Revenue per Charger in $")
    plt.title("Revenue per Charger")
    plt.show()
    fig.savefig(fname, bbox_inches='tight', pad_inches=0.1)
    # average cost per km
    pfname = path_file_name(AS_PATH, model, nbr_of_agents, "avg", "cost",
                            "png")
    fig, ax = plt.subplots()
    ax.plot(x_data, data_dict["avg_cost_apartment"],
            label="avg_cost_apartment")
    ax.plot(x_data, data_dict["avg_cost_house_pv"], 
            label="avg_cost_house_pv")
    ax.plot(x_data, data_dict["avg_cost_house_no_pv"],
            label="avg_cost_house_no_pv")
    ax.plot(x_data, data_dict["avg_cost"],
            label="avg_cost")
    ax.set(xlabel=x_label, ylabel="$/km")
    plt.legend()
    plt.title("Average cost per km")
    plt.show()
    fig.savefig(pfname, bbox_inches='tight', pad_inches=0.1)
            
def plot_2D_sweep_results(identifier, header, front_col, data, pf_name):
    cast = Cast("average_season")
    y_label = header.split(',')[0].split('\\')[0]
    x_label = header.split(',')[0].split('\\')[1]
    x_ticks = [cast.to_float(header_element, "header element")
               for header_element in header.split(',')[1:]]
    y_ticks = [cast.to_int(front_col_element, "front col element")
               for front_col_element in front_col]
    cmap = mpl.cm.viridis
    fig, ax = plt.subplots()
    vmin=min([min(row) for row in data])
    vmax=max([max(row) for row in data])
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    ax.pcolormesh(x_ticks, y_ticks, data, cmap=cmap, shading='gouraud',
                  vmin=vmin, vmax=vmax)
    ax.set(xlabel=x_label, ylabel=y_label)
    
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),
                        cax=cax)
    cbar.set_label(identifier)
    
    ax.set_title(identifier)
    plt.show()
    fig.savefig(pf_name, bbox_inches='tight', pad_inches=0.1)
    
def decide_what_to_do(co, identifiers, title, seasons, sweep_dimension,
                      model, nbr_of_agents):
    nbr_missing_files, missing_files \
        = determine_missing_files(identifiers, seasons, model, nbr_of_agents)
    if nbr_missing_files == 0:
        handle_averaging_all_identifiers(identifiers, sweep_dimension,
                                         model, nbr_of_agents)
        co.t_print("Averaged {}".format(title))
    elif nbr_missing_files != len(identifiers) * len(seasons):
        co.t_print("Files missing to average {}:".format(title))
        for _identifier, _seasons in missing_files.items():
            co.t_print("{} misses seasons: {}".format(_identifier, _seasons))
    else:
        # no files to average for Single-Run-Session
        return False
    return True

def exec_avg(model, nbr_of_agents, plot_results=True):
    no_files_found = True
    # Average Single-Run-Session
    files_found = decide_what_to_do(AS_co, AS_SINGLE_RUN, "Single-Run-Session",
                                    AS_SEASONS, 0, model, nbr_of_agents)
    if files_found: no_files_found = False
    
    # Average 1-Dimensional-Sweep
    files_found = decide_what_to_do(AS_co, AS_D1_SWEEP, "1-Dimensional-Sweep", 
                                    AS_SEASONS, 1, model, nbr_of_agents)
    if files_found: no_files_found = False
    
    # Average 2-Dimensional-Sweep
    files_found = decide_what_to_do(AS_co, AS_D2_SWEEP, "2-Dimensional-Sweep",
                                    AS_SEASONS, 2, model, nbr_of_agents)
    if files_found: no_files_found = False
    
    if no_files_found:
        AS_co.t_print("No matching set of files found!")
    

# formated output
AS_co = ConsoleOutput()

# constants
AS_SINGLE_RUN = ["charge_received_time_series",
              "charger_utilisation_time_series",
              "location_time_series"]
AS_D1_SWEEP = ["sweep_data"]
AS_D2_SWEEP = ["avg_cost", "avg_cost_apartment", "avg_cost_house_no_pv",
            "avg_cost_house_pv", "charge_emergency", "charge_grid",
            "charge_held_back", "charge_pv", "charge_work", "utilisation"]
AS_PATH = "results"
AS_SEASONS = [0,1,2,3]

if __name__ == "__main__":
    model = 6
    nbr_of_agents = 12000
    exec_avg(model, nbr_of_agents)