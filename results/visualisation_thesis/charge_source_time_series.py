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

# moving average over maw time steps
maw = 2*12

data_set_name = ["charge_received_grid", "charge_received_public",
            "charge_received_pv", "charge_received_work"]
labels = ["Grid", "Public", "PV", "Work"]
colors = ['k','b', 'g', 'r']

#model 1 (nw) low price (lp)
file_m1_lp = "model_10_nbr_agents_12000_26c_season_avg_charge_received_time_series.csv"
#model 4 (bc) low price (lp)
file_m4_lp = "model_9_nbr_agents_12000_26c_season_avg_charge_received_time_series.csv"
#model 4 (bc) high price (hp)
file_m4_hp = "model_9_nbr_agents_12000_28c_season_avg_charge_received_time_series.csv"
#model 6 (ac) low price (lp)
file_m6_lp = "model_8_nbr_agents_12000_26c_season_avg_charge_received_time_series.csv"
#model 6 (ac) high price (hp)
file_m6_hp = "model_8_nbr_agents_12000_28c_season_avg_charge_received_time_series.csv"

names = ["m1_lp","m4_lp","m4_hp","m6_lp","m6_hp"]
files = [file_m1_lp, file_m4_lp, file_m4_hp, file_m6_lp, file_m6_hp]
            
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
            front_col.append(cast.to_int(row[0], "x_value") / 60 - 24 * 7)
            data.append([cast.to_float(cell, "data_cell") for cell in row[1:]])
    return first_row, front_col, data

def plot_data(ax, labeltext, x_pos, y_pos, model, x_labels, y_labels, linewidth, fontsize):
    dm = data[model]
    for i, ds in enumerate(data_set_name):    
        ax[y_pos,x_pos].plot(dm["x_value"], dm[ds], label=labels[i],
                             linewidth=linewidth, color=colors[i])
        avg = sum(dm[ds]) / len(dm[ds])
        ax[y_pos,x_pos].plot([dm["x_value"][0], dm["x_value"][-1]], [avg, avg],
                             linewidth=linewidth, color=colors[i],
                             linestyle='--')
    
    if x_labels:
        ax[y_pos,x_pos].set_xlabel(x_label, fontsize=fontsize)
        ax[y_pos,x_pos].xaxis.set_minor_locator(AutoMinorLocator())
    else:
        ax[y_pos,x_pos].set_xticklabels("", fontsize=fontsize)
    if y_labels:
        ax[y_pos,x_pos].set_ylabel(y_label, fontsize=fontsize)
    ax[y_pos,x_pos].set_xticks(range(0, 24*8, 24))
    ax[y_pos,x_pos].set_xlim(0,167)
    ax[y_pos,x_pos].set_yscale('log')
    ax[y_pos,x_pos].set_ylim(5*10**0,9*10**6)
    ax[y_pos,x_pos].grid(True)
    if not y_labels:
        for tick in ax[y_pos,x_pos].yaxis.get_major_ticks():
            tick.tick1line.set_visible(False)
            tick.tick2line.set_visible(False)
            tick.label1.set_visible(False)
            tick.label2.set_visible(False)

        ax[y_pos,x_pos].yaxis.set_minor_locator(AutoMinorLocator())
    ax[y_pos,x_pos].grid(True)
    ax[y_pos,x_pos].tick_params(labelsize=fontsize)
    ax[y_pos,x_pos].text(164, 6.5*10**6, labeltext[0], va="top", ha="right",
                         fontsize=fontsize)
    ax[y_pos,x_pos].text(4, 7*10**6, labeltext[1], va="top", ha="left",
                         fontsize=fontsize)

data_raw = dict()
first_row = dict()
front_col = dict()
for it, name in enumerate(names):
    first_row[name], front_col[name], data_tmp = read_data(PATH, files[it])
    data_raw[name] = dict()
    for it, first_row_cell in enumerate(first_row[name]):
        if it == 0:
            data_raw[name]["x_value"] = front_col[name]
        else:
            data_raw[name][first_row_cell] = []
            for data_row in data_tmp:
                data_raw[name][first_row_cell].append(data_row[it-1]*12*100)

# moving average
data = dict()
for name, data_set in data_raw.items():
    data[name] = dict()
    for col_name, col_data in data_set.items():
        if col_name == "x_value":
            data[name][col_name] = col_data
        else:
            data[name][col_name] = []
            for it, value in enumerate(col_data):
                start_it = it - maw // 2
                end_it = start_it + maw
                _sum = 0
                for i in range(0, maw):
                    _sum += col_data[(start_it + i) % len(col_data)]
                avg_value = _sum / maw
                data[name][col_name].append(avg_value)

cast = Cast("Analysis")

x_label = "$t$ in h"
y_label = "$P_{\u2020,\u26AA}$ in kW"

label_fig_a = ("$p^w$ = 0.26 \$/kWh\n adv","a)")
label_fig_b = ("$p^w$ = 0.26 \$/kWh\n bsc","b)")
label_fig_c = ("$p^w$ = 0.28 \$/kWh\n adv","c)")
label_fig_d = ("$p^w$ = 0.28 \$/kWh\n bsc","d)")
label_fig_e = ("nw","e)")

linewidth = .6
cm = 1/2.54
fontsize=8

fig = plt.figure(figsize=(14.6*cm, 10*cm))
gs = fig.add_gridspec(2, 3, hspace=0, wspace=0)
ax = gs.subplots(sharex=False, sharey=False)

plot_data(ax, label_fig_a, 0, 0, "m6_lp", False, True, linewidth, fontsize)
plot_data(ax, label_fig_c, 0, 1, "m6_hp", True, True, linewidth, fontsize)
plot_data(ax, label_fig_b, 1, 0, "m4_lp", False, False, linewidth, fontsize)
plot_data(ax, label_fig_d, 1, 1, "m4_hp", True, False, linewidth, fontsize)
plot_data(ax, label_fig_e, 2, 1, "m1_lp", True, False, linewidth, fontsize)

ln_grid, = ax[0, 2].plot([0, 1], [0, 1], linewidth=linewidth, color='k')
ln_pv, = ax[0, 2].plot([0, 1], [0, 1], linewidth=linewidth, color='g')
ln_work, = ax[0, 2].plot([0, 1], [0, 1], linewidth=linewidth, color='r')
ln_publ, = ax[0, 2].plot([0, 1], [0, 1], linewidth=linewidth, color='b')
ln_ts, = ax[0, 2].plot([0, 1], [0, 1], linewidth=linewidth, color='k')
ln_avg, = ax[0, 2].plot([0, 1], [0, 1], linewidth=linewidth, color='k',
                       linestyle='--')
ax[0, 2].set_xlim(2,3)
ax[0, 2].set_ylim(2,3)
ax[0, 2].set_axis_off()
leg1 = ax[0, 2].legend([ln_grid, ln_pv, ln_work, ln_publ],
                       ["Grid", "PV", "Work", "Public"],fontsize=fontsize,
                       loc="upper center")
leg2 = ax[0, 2].legend([ln_ts, ln_avg], ["Time series","Average"],
                       fontsize=fontsize, loc="lower center")
ax[0, 2].add_artist(leg1)

plt.show()

file_name = "charge_source_time_series.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "charge_source_time_series.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)