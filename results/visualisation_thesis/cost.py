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
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)


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

#model 4
file_m4 = "model_4_nbr_agents_6000_season_avg_sweep_data.csv"
#model 6
file_m6 = "model_6_nbr_agents_6000_season_avg_sweep_data.csv"

names = ["m4","m6"]
files = [file_m4, file_m6]
            
def read_data(relative_path, file_name):
    cast = Cast("difference_tool")
    csv_helper = CSVHelper(relative_path, file_name, skip_header=False)
    first_row = csv_helper.data[0]
    front_col, data = [], []
    for row in csv_helper.data[1:]:
        front_col.append(cast.to_float(row[0], "x_value"))
        data.append([cast.to_float(cell, "data_cell") for cell in row[1:]])
    return first_row, front_col, data

data = dict()
data_diff = dict()
first_row = dict()
front_col = dict()
for it, name in enumerate(names):
    first_row[name], front_col[name], data_tmp = read_data(PATH, files[it])
    data[name] = dict()
    for it, first_row_cell in enumerate(first_row[name]):
        if it == 0:
            data[name]["x_value"] = front_col[name]
        else:
            data[name][first_row_cell] = []
            for data_row in data_tmp:
                data[name][first_row_cell].append(data_row[it-1]*100)

data_diff["x_value"] = data["m6"]["x_value"]
data_diff["diff"] = [(data["m4"]["avg_cost"][it] - data["m6"]["avg_cost"][it]) *10
                     for it in range(0, len(data_diff["x_value"]))]

cast = Cast("Analysis")

x_label = "$p^w$ in \$/kWh"
y_label = "$C_{\u2020,\u2217}$ in \n$10^{-2}$ \$/km"
y_label_small = "$C_{\u2020}$ in \n $10^{-2}$ \$/km"
y_label_diff = "$C_{bsc} - C_{adv}$ in \n $10^{-3}$ \$/km"

linewidth = .8
cm = 1/2.54
fontsize=8

fig = plt.figure(figsize=(3.5, 9*cm))
heights = [4, 3, 3]
gs = fig.add_gridspec(3, 1, hspace=0*cm, height_ratios=heights)
ax = gs.subplots(sharex=True, sharey=False)


line1, = ax[0].plot(data["m6"]["x_value"], data["m6"]["avg_cost_apartment"], label="m6 apt", linewidth=linewidth, color="b")
ax[0].plot(data["m4"]["x_value"], data["m4"]["avg_cost_apartment"], label="m4 apt", linewidth=linewidth, color="b", linestyle='--')
line2, = ax[0].plot(data["m6"]["x_value"], data["m6"]["avg_cost_house_no_pv"], label="m6 noPV", linewidth=linewidth, color="r")
ax[0].plot(data["m4"]["x_value"], data["m4"]["avg_cost_house_no_pv"], label="m4 npPV", linewidth=linewidth, color="r", linestyle='--')
line3, = ax[0].plot(data["m6"]["x_value"], data["m6"]["avg_cost_house_pv"], label="m6 PV", linewidth=linewidth, color="g")
ax[0].plot(data["m4"]["x_value"], data["m4"]["avg_cost_house_pv"], label="m4 PV", linewidth=linewidth, color="g", linestyle='--')
ax[0].set_xlabel(x_label, fontsize=fontsize)
ax[0].xaxis.set_minor_locator(AutoMinorLocator())
ax[0].set_ylabel(y_label, fontsize=fontsize)
ax[0].yaxis.set_minor_locator(AutoMinorLocator())
ax[0].grid(True)
ax[0].tick_params(labelsize=fontsize)
ax[0].legend([line1, line2, line3], ['Apartment', 'House without PV', 'House with PV'], fontsize=fontsize, loc=2)
ax[0].text(.33, .4, "a)", va="bottom", ha="right", fontsize=fontsize)

ax[1].plot(data["m6"]["x_value"], data["m6"]["avg_cost"], label="adv", linewidth=linewidth, color="k")
ax[1].plot(data["m4"]["x_value"], data["m4"]["avg_cost"], label="bsc", linewidth=linewidth, color="k", linestyle='--')
ax[1].set_xlabel(x_label, fontsize=fontsize)
ax[1].xaxis.set_minor_locator(AutoMinorLocator())
ax[1].set_ylabel(y_label_small, fontsize=fontsize)
ax[1].yaxis.set_minor_locator(AutoMinorLocator())
ax[1].grid(True)
ax[1].tick_params(labelsize=fontsize)
ax[1].legend(fontsize=fontsize, loc=4)
ax[1].text(.03, 4.8, "b)", va="top", ha="left", fontsize=fontsize)

ax[2].plot(data_diff["x_value"], data_diff["diff"], label="m6", linewidth=linewidth, color="k")
ax[2].set_xlabel(x_label, fontsize=fontsize)
ax[2].xaxis.set_minor_locator(AutoMinorLocator())
ax[2].set_ylabel(y_label_diff, fontsize=fontsize)
ax[2].set_yticks([0,1])
ax[2].set_yticklabels([0,1])
ax[2].yaxis.set_minor_locator(AutoMinorLocator())
ax[2].grid(True)
ax[2].tick_params(labelsize=fontsize)
ax[2].text(.03, 1.8, "c)", va="top", ha="left", fontsize=fontsize)

plt.show()

file_name = "cost.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "cost.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)