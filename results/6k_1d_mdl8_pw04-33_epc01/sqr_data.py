# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 14:00:30 2021

@author: S3739258
"""

import os
import fiona

import matplotlib.pyplot as plt
import matplotlib.patches
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable


from parameters import Parameters
from output_data import OutputData
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
nbr_of_agents = 2400
# run A
season = "1"
model = 6
addendum = ""
identifier = "avg_cost"

# use moving avg? (0 is no)
half_avg_over = 10
plot_all_time_steps_to_map = False

frmt = lambda lst : str(lst[0]) + "-" + str(lst[1])

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

def get_color(cmap, value, min_value, max_value):
    _max = max(abs(min_value), max_value)
    rel_value = 0.5 + value / _max
    return list(cmap(rel_value))[:3]
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
            data.append([pow(cast.to_float(cell, "data_cell"),3) for cell in row[1:]])
    return first_row, front_col, data

def analyse_2d_sweep_diff(identifiers, first_row, front_col, data_diff):
    cast = Cast("Analysis")
    cmap = mpl.cm.viridis
    for identifier in identifiers:
        print(identifier)
        x_label = first_row[0].split('\\')[1]
        y_label = first_row[0].split('\\')[0]
        x_ticks = [cast.to_float(i, "first_row_cell")\
                   for i in first_row[1:]]
        y_ticks = [cast.to_int(i, "front_col_cell")\
                   for i in front_col]
        fig, ax = plt.subplots()
        vmin=min([min(row) for row in data_diff])
        vmax=max([max(row) for row in data_diff])
        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
        ax.pcolormesh(x_ticks, y_ticks, data_diff, cmap=cmap,
                      shading='gouraud', vmin=vmin, vmax=vmax)
        ax.set(xlabel=x_label, ylabel=y_label)
        
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),
                            cax=cax)
        cbar.set_label(identifier)
        
        ax.set_title(identifier)
        plt.show()
        
        pf_name = path_file_name(model, nbr_of_agents, season,
                                 "sqr_", identifier, "png")
        fig.savefig(pf_name, bbox_inches='tight', pad_inches=0.1)


f_name = file_name(model, nbr_of_agents, season, identifier, addendum, ".csv")        
first_row, front_col, data = read_data(PATH, f_name)

analyse_2d_sweep_diff([identifier], first_row, front_col, data)