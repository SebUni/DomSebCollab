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
import matplotlib.gridspec as gridspec


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
#model 6 PV only
file_m6_PV = "model_6_PV_only_nbr_agents_6000_season_avg_sweep_data.csv"

names = ["m4","m6","m6PV"]
files = [file_m4, file_m6, file_m6_PV]
            
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
            front_col.append(cast.to_float(row[0], "x_value"))
            data.append([cast.to_float(cell, "data_cell") for cell in row[1:]])
    return first_row, front_col, data

data = dict()
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
                if first_row_cell in ["charge_grid", "charge_held_back", "charge_pv", "charge_work"]:
                    data[name][first_row_cell].append(data_row[it-1]/10**5)
                elif first_row_cell == "total_revenue":
                    data[name][first_row_cell].append(data_row[it-1]/10**4)
                else:
                    data[name][first_row_cell].append(data_row[it-1])

cast = Cast("Analysis")

x_label = "$p^w$ in \$/kWh"
y_label_charge = "$E_{\u2020,\u26AA}$ in 10 GWh"
y_label_revenue = "$R_{\u2020,\u2217}$ in \$$10^6$"
y_label_utilisation = "$U_{\u2020,\u2217}$ in %"

linewidth = 1
cm = 1/2.54
fontsize=8

fig = plt.figure(figsize=(3.5, 9*cm))

gs0 = gridspec.GridSpec(2, 1, figure=fig, hspace=0, wspace=0*cm,
                        height_ratios=[.45,.55])
gs00 = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs0[0], wspace=0)

ax_charge = fig.add_subplot(gs00[0, 0])
ax_charge_PV = fig.add_subplot(gs00[0, 1], sharex=ax_charge)

# the following syntax does the same as the GridSpecFromSubplotSpec call above:
gs01 = gs0[1].subgridspec(2, 2, wspace=0, hspace=0)

ax_ut = fig.add_subplot(gs01[1, 0])
ax_ut_PV = fig.add_subplot(gs01[1, 1])
ax_rev = fig.add_subplot(gs01[0, 0])
ax_rev_PV = fig.add_subplot(gs01[0, 1])

# ax_ut = fig.add_subplot(gs01[1, 0])
# ax_ut_PV = fig.add_subplot(gs01[1, 1], sharex=ax_ut, sharey=ax_ut)
# ax_rev = fig.add_subplot(gs01[0, 0], sharex=ax_ut)
# ax_rev_PV = fig.add_subplot(gs01[0, 1], sharex=ax_ut, sharey=ax_rev)

line1, = ax_charge.plot(data["m6"]["x_value"], data["m6"]["charge_grid"], label="m6 Grid", linewidth=linewidth, color="k")
line2, = ax_charge.plot(data["m4"]["x_value"], data["m4"]["charge_grid"], label="m4 Grid", linewidth=linewidth, color="k", linestyle='--')

line1_PV, = ax_charge_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["charge_grid"], label="m6 Grid", linewidth=linewidth, color="k")
line2_PV, = ax_charge_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["charge_pv"], label="m6 PV", linewidth=linewidth, color="g")
line3_PV, = ax_charge_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["charge_work"], label="m6 Work", linewidth=linewidth, color="r")
line4_PV, = ax_charge_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["charge_held_back"], label="m6 HeldB", linewidth=linewidth, color="orange")

ax_charge.plot(data["m6"]["x_value"], data["m6"]["charge_pv"], label="m6 PV", linewidth=linewidth, color="g")
ax_charge.plot(data["m4"]["x_value"], data["m4"]["charge_pv"], label="m4 PV", linewidth=linewidth, color="g", linestyle='--')
ax_charge.plot(data["m6"]["x_value"], data["m6"]["charge_work"], label="m6 Work", linewidth=linewidth, color="r")
ax_charge.plot(data["m4"]["x_value"], data["m4"]["charge_work"], label="m4 Work", linewidth=linewidth, color="r", linestyle='--')
ax_charge.plot(data["m6"]["x_value"], data["m6"]["charge_held_back"], label="m6 HeldB", linewidth=linewidth, color="orange")
ax_charge.plot(data["m4"]["x_value"], data["m4"]["charge_held_back"], label="m4 HeldB", linewidth=linewidth, color="orange", linestyle='--')
ax_charge.set_xlabel(x_label, fontsize=fontsize)
ax_charge.xaxis.set_minor_locator(AutoMinorLocator())
ax_charge.set_yticks([0, 1, 2])
ax_charge.set_ylim([-0.1, 2.1])
ax_charge.set_ylabel(y_label_charge, fontsize=fontsize)
ax_charge.yaxis.set_minor_locator(AutoMinorLocator())
ax_charge.grid(True)
ax_charge.tick_params(labelsize=fontsize)
ax_charge.legend([line1_PV, line2_PV, line3_PV, line4_PV],
                 ['Grid', 'PV', 'Work', 'HB'],
                 fontsize=fontsize, loc=6) # , bbox_to_anchor=(1, .55))
ax_charge.text(.33, 2, "a)", va="top", ha="right", fontsize=fontsize)

ax_charge_PV.set_xlabel(x_label, fontsize=fontsize)
ax_charge_PV.xaxis.set_minor_locator(AutoMinorLocator())
ax_charge_PV.set_yticks([0, 1, 2])
ax_charge_PV.set_ylim([-0.1, 2.1])
ax_charge_PV.yaxis.set_minor_locator(AutoMinorLocator())
ax_charge_PV.set_yticklabels([])
ax_charge_PV.yaxis.tick_right()
ax_charge_PV.grid(True)
ax_charge_PV.tick_params(labelsize=fontsize)
ax_charge_PV.yaxis.set_ticks_position('none')
ax_charge_PV.legend([line1, line2], ['adv', 'bsc'], fontsize=fontsize, loc=7)
ax_charge_PV.text(.33, 2, "b)", va="top", ha="right", fontsize=fontsize)

ax_ut.plot(data["m6"]["x_value"], data["m6"]["utilisation"], label="m6 Ut", linewidth=linewidth, color="k")
ax_ut.plot(data["m4"]["x_value"], data["m4"]["utilisation"], label="m4 Ut", linewidth=linewidth, color="k", linestyle='--')
ax_ut.set_xlabel(x_label, fontsize=fontsize)
ax_ut.xaxis.set_minor_locator(AutoMinorLocator())
ax_ut.set_yticks([0, 1, 2])
ax_ut.set_ylim([-0.1, 2.4])
# ax_charge_PV.set_yticklabels([])
# ax_charge_PV.yaxis.tick_right()
ax_ut.set_ylabel(y_label_utilisation, fontsize=fontsize)
ax_ut.yaxis.set_minor_locator(AutoMinorLocator())
ax_ut.grid(True)
ax_ut.tick_params(labelsize=fontsize)
# ax_charge.legend(fontsize=fontsize, loc=2)
ax_ut.text(.04, 0, "e)", va="bottom", ha="left", fontsize=fontsize)

ax_ut_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["utilisation"], label="m6 Ut", linewidth=linewidth, color="k")
ax_ut_PV.set_xlabel(x_label, fontsize=fontsize)
ax_ut_PV.xaxis.set_minor_locator(AutoMinorLocator())
ax_ut_PV.set_yticklabels([])
ax_ut_PV.set_ylim(ax_ut.get_ylim())
ax_ut_PV.yaxis.set_minor_locator(AutoMinorLocator())
ax_ut_PV.grid(True)
ax_ut_PV.tick_params(labelsize=fontsize)
ax_ut_PV.yaxis.set_ticks_position('none')
ax_ut_PV.text(.04, 0, "f)", va="bottom", ha="left", fontsize=fontsize)

ax_rev.plot(data["m6"]["x_value"], data["m6"]["total_revenue"], label="m6 Rev", linewidth=linewidth, color="k")
ax_rev.plot(data["m4"]["x_value"], data["m4"]["total_revenue"], label="m4 Rev", linewidth=linewidth, color="k", linestyle='--')
ax_rev.xaxis.set_minor_locator(AutoMinorLocator())
ax_rev.set_xticklabels([])
ax_rev.set_ylim([-0.2, 5.4])
ax_rev.set_ylabel(y_label_revenue, fontsize=fontsize)
ax_rev.yaxis.set_minor_locator(AutoMinorLocator())
ax_rev.grid(True)
ax_rev.tick_params(labelsize=fontsize)
ax_rev.xaxis.set_ticks_position('none')
ax_rev.text(.04, 5, "c)", va="top", ha="left", fontsize=fontsize)

ax_rev_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["total_revenue"], label="m6 Rev", linewidth=linewidth, color="k")
ax_rev_PV.xaxis.set_minor_locator(AutoMinorLocator())
ax_rev_PV.yaxis.set_minor_locator(AutoMinorLocator())
ax_rev_PV.set_yticks(ax_rev.get_yticks())
ax_rev_PV.set_ylim(ax_rev.get_ylim())
ax_rev_PV.grid(True)
ax_rev_PV.xaxis.set_ticks_position('none')
ax_rev_PV.set_xticklabels([])
ax_rev_PV.yaxis.set_ticks_position('none')
ax_rev_PV.set_yticklabels([])
ax_rev_PV.text(.04, 5, "d)", va="top", ha="left", fontsize=fontsize)

plt.show()

file_name = "one_week_charge_ut_rev.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "one_week_charge_ut_rev.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)