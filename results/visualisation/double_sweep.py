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
mpl.rcParams['figure.dpi'] = 300

# ### comparison parameters
# general
nbr_of_agents = 2400
# run A
season = "1"
model = 6
addendum = ""
identifier = "avg_cost"

file_left = "model_6_nbr_agents_2400_season_avg_avg_cost.csv"
file_right = "model_4-6_nbr_agents_2400_season_avg-avg_-_diff_avg_cost.csv"
            
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


cast = Cast("Analysis")

first_row_left,  front_col_left,  data_left  = read_data(PATH, file_left)
first_row_right, front_col_right, data_right = read_data(PATH, file_right)

for i, _ in enumerate(data_left):
    for j, __ in enumerate(_):
        data_left[i][j] *= 10**2
for i, _ in enumerate(data_right):
    for j, __ in enumerate(_):
        data_right[i][j] *= 10**2

cmap = mpl.cm.viridis
x_label_left = "$p^w$ in \$/kWh"
x_label_right = "$p^w$ in \$/kWh"
y_label_left = "Employees per charger"
y_label_right = "Employees per charger"
z_label_left = "$C^{avg}_{adv}$ in $10^{-2}$ \$/km"
z_label_right = "$C^{avg}_{bsc} - C^{avg}_{adv}$ in $10^{-2}$ \$/km"

x_ticks_left = [cast.to_float(i, "first_row_cell")\
                for i in first_row_left[1:]]
x_ticks_right = [cast.to_float(i, "first_row_cell")\
                 for i in first_row_right[1:]]
y_ticks_left = [cast.to_int(i, "front_col_cell") \
                for i in front_col_left]
y_ticks_right = [cast.to_int(i, "front_col_cell") \
                 for i in front_col_right]

cm = 1/2.54
fontsize=8

fig = plt.figure(figsize=(16*cm, 5*cm))
gs = fig.add_gridspec(1, 2, wspace=1.3*cm)
ax = gs.subplots(sharex=False, sharey=False)

vmin_left=min([min(row) for row in data_left])
vmin_right=min([min(row) for row in data_right])
vmax_left=max([max(row) for row in data_left])
vmax_right=max([max(row) for row in data_right])
norm_left = mpl.colors.Normalize(vmin=vmin_left, vmax=vmax_left)
norm_right = mpl.colors.Normalize(vmin=vmin_left, vmax=vmax_right)

ax[0].pcolormesh(x_ticks_left, y_ticks_left, data_left, cmap=cmap,
              shading='gouraud', vmin=vmin_left, vmax=vmax_left)
ax[0].set_xlabel(x_label_left, fontsize=fontsize)
ax[0].set_ylabel(y_label_left, fontsize=fontsize)
ax[0].minorticks_on()
ax[0].tick_params(labelsize=fontsize)

divider = make_axes_locatable(ax[0])
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm_left,cmap=cmap),
                    cax=cax)
cbar.minorticks_on()
cbar.ax.tick_params(labelsize=fontsize)
cbar.set_label(z_label_left, fontsize=fontsize)
ax[0].text(.32, 81, "a)", va="top", ha="right", fontsize=fontsize)

ax[1].pcolormesh(x_ticks_right, y_ticks_right, data_right, cmap=cmap,
              shading='gouraud', vmin=vmin_right, vmax=vmax_right)
ax[1].set_xlabel(x_label_right, fontsize=fontsize)
ax[1].set_ylabel(y_label_right, fontsize=fontsize)
ax[1].minorticks_on()
ax[1].tick_params(labelsize=fontsize)
ax[1].text(.32, 81, "b)", va="top", ha="right", fontsize=fontsize, color='w')

divider = make_axes_locatable(ax[1])
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm_right,cmap=cmap),
                    cax=cax)
cbar.minorticks_on()
cbar.ax.tick_params(labelsize=fontsize)
cbar.set_label(z_label_right, fontsize=fontsize)

plt.show()

file_name = "double_sweep.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "double_sweep.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)