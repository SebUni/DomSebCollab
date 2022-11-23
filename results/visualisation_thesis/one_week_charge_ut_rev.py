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
file_m4 = "model_9_nbr_agents_6000_season_avg_sweep_data.csv"
#model 6
file_m6 = "model_8_nbr_agents_6000_season_avg_sweep_data.csv"
#model 6 PV only
file_m6_PV = "model_8_nbr_agents_6000_season_avg_sweep_data_PVonly.csv"

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

def format_subplot(axes: mpl.axes, fig_lbl_pos: tuple, fig_lbl_txt: str,
                   ticks=(None, None), lims=(None, None),
                   ax_lbls=(None, None)):
    show_ticks = [s is not None for s in ax_lbls]
    axes.xaxis.set_minor_locator(AutoMinorLocator())
    axes.yaxis.set_minor_locator(AutoMinorLocator())
    set_tuple(axes, "ticks", ticks)
    set_tuple(axes, "lim", lims)
    axes.grid(True)
    axes.xaxis.set_ticks_position('default' if show_ticks[0] else 'none')
    axes.yaxis.set_ticks_position('default' if show_ticks[1] else 'none')
    set_tuple(axes, "ticklabels", ([] if not s else None for s in show_ticks))
    set_tuple(axes, "label", ax_lbls, kwargs={"fontsize": fontsize})
    lims = get_lims(axes)
    lbl_pos = [l[0] + (l[1] - l[0]) * lp for l, lp in zip (lims, fig_lbl_pos)]
    axes.text(*lbl_pos, fig_lbl_txt, va="top", ha="left", fontsize=fontsize)
    axes.tick_params(labelsize=fontsize, which="both", top=False, right=False)
    
def set_tuple(clss: object, meth: str, tup: tuple, kwargs=dict()):
    for a, t in zip(('x', 'y'), tup):
        if t is not None:
            getattr(clss, "set_" + a + meth)(t, **kwargs)

def get_ticks(axes: mpl.axes):
    return (axes.get_xticks(), axes.get_yticks())

def get_lims(axes: mpl.axes):
    return (axes.get_xlim(), axes.get_ylim())

data = dict()
first_row = dict()
front_col = dict()
for it, name in enumerate(names):
    first_row[name], front_col[name], data_tmp = read_data(PATH, files[it])
    data[name] = dict()
    data[name]["x_value"] = front_col[name]
    for it, first_row_cell in enumerate(first_row[name][1:]):
        data[name][first_row_cell] = []
        for data_row in data_tmp:
            if first_row_cell in ["charge_grid", "charge_held_back",
                                  "charge_pv", "charge_work",
                                  "charge_emergency"]:
                data[name][first_row_cell].append(data_row[it]/10**5)
            elif first_row_cell == "total_revenue":
                data[name][first_row_cell].append(data_row[it]/10**4)
            else:
                data[name][first_row_cell].append(data_row[it])

cast = Cast("Analysis")

x_label = "$p^w$ in \$/kWh"
y_label_charge = "$E_{\u2020,\u26AA}$ in 10 GWh"
y_label_charge_apt = "$E_{\u2020,\u26AA,hPV}$ in 10 GWh"
y_label_revenue = "$R_{\u2020}$ in \$$10^6$"
y_label_revenue_apt = "$R_{\u2020,hPV}$ in \$$10^6$"
y_label_utilisation = "$U_{\u2020}$ in %"
y_label_utilisation_apt = "$U_{\u2020,hPV}$ in %"

linewidth = 1
cm = 1/2.54
fontsize=8

fig = plt.figure(figsize=(14.6*cm, 9*cm))

gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0*cm, wspace=1*cm,
                        height_ratios=[.45,.275,.275])

ax_charge = fig.add_subplot(gs[0, 0])
ax_charge_PV = fig.add_subplot(gs[0, 1])
ax_rev = fig.add_subplot(gs[1, 0])
ax_rev_PV = fig.add_subplot(gs[1, 1])
ax_ut = fig.add_subplot(gs[2, 0])
ax_ut_PV = fig.add_subplot(gs[2, 1])

# ax_ut = fig.add_subplot(gs01[1, 0])
# ax_ut_PV = fig.add_subplot(gs01[1, 1], sharex=ax_ut, sharey=ax_ut)
# ax_rev = fig.add_subplot(gs01[0, 0], sharex=ax_ut)
# ax_rev_PV = fig.add_subplot(gs01[0, 1], sharex=ax_ut, sharey=ax_rev)

line1, = ax_charge.plot(data["m6"]["x_value"], data["m6"]["charge_grid"], label="m6 Grid", linewidth=linewidth, color="k")
line1b, = ax_charge.plot(data["m4"]["x_value"], data["m4"]["charge_grid"], label="m4 Grid", linewidth=linewidth, color="k", linestyle='--')
line2, = ax_charge.plot(data["m6"]["x_value"], data["m6"]["charge_pv"], label="m6 PV", linewidth=linewidth, color="g")
ax_charge.plot(data["m4"]["x_value"], data["m4"]["charge_pv"], label="m4 PV", linewidth=linewidth, color="g", linestyle='--')
line3, =ax_charge.plot(data["m6"]["x_value"], data["m6"]["charge_work"], label="m6 Work", linewidth=linewidth, color="r")
ax_charge.plot(data["m4"]["x_value"], data["m4"]["charge_work"], label="m4 Work", linewidth=linewidth, color="r", linestyle='--')
line4, = ax_charge.plot(data["m6"]["x_value"], data["m6"]["charge_held_back"], label="m6 HeldB", linewidth=linewidth, color="orange")
ax_charge.plot(data["m4"]["x_value"], data["m4"]["charge_held_back"], label="m4 HeldB", linewidth=linewidth, color="orange", linestyle='--')
#ax_charge.plot(data["m6"]["x_value"], data["m6"]["charge_emergency"], label="m6 HeldB", linewidth=linewidth, color="orange")
#ax_charge.plot(data["m4"]["x_value"], data["m4"]["charge_emergency"], label="m4 HeldB", linewidth=linewidth, color="orange", linestyle='--')
ax_charge.legend([line1, line2, line3, line4],
                 ['Grid', 'PV', 'Work', 'Held back'],
                 fontsize=fontsize, loc=6) # , bbox_to_anchor=(1, .55))
format_subplot(ax_charge, (.9, .95), "a)",
               ticks=(None, [0, 1, 2]),
               lims=(None, [-0.1, 2.35]),
               ax_lbls=(None, y_label_charge))

ax_charge_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["charge_grid"], label="m6 Grid", linewidth=linewidth, color="k")
ax_charge_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["charge_pv"], label="m6 PV", linewidth=linewidth, color="g")
ax_charge_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["charge_work"], label="m6 Work", linewidth=linewidth, color="r")
ax_charge_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["charge_held_back"], label="m6 HeldB", linewidth=linewidth, color="orange")
#ax_charge_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["charge_emergency"], label="m6 public", linewidth=linewidth, color="orange")
ax_charge_PV.legend([line1, line1b], ['adv', 'bsc'], fontsize=fontsize, loc=7)
format_subplot(ax_charge_PV, (.9, .95), "b)",
               ticks=get_ticks(ax_charge),
               lims=get_lims(ax_charge),
               ax_lbls=(None, y_label_charge_apt))

ax_rev.plot(data["m6"]["x_value"], data["m6"]["total_revenue"], label="m6 Rev",
            linewidth=linewidth, color="k")
ax_rev.plot(data["m4"]["x_value"], data["m4"]["total_revenue"], label="m4 Rev",
            linewidth=linewidth, color="k", linestyle='--')
format_subplot(ax_rev, (.9, .9), "c)",
               ticks=(None, [0,2,4,6]),
               lims=(None, [-0.2, 6.5]),
               ax_lbls=(None, y_label_revenue))

ax_rev_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["total_revenue"],
               label="m6 Rev", linewidth=linewidth, color="k")
format_subplot(ax_rev_PV, (.9, .9), "d)",
               ticks=get_ticks(ax_rev),
               lims=get_lims(ax_rev),
               ax_lbls=(None, y_label_revenue_apt))

ax_ut.plot(data["m6"]["x_value"], data["m6"]["utilisation"], label="m6 Ut",
           linewidth=linewidth, color="k")
ax_ut.plot(data["m4"]["x_value"], data["m4"]["utilisation"], label="m4 Ut",
           linewidth=linewidth, color="k", linestyle='--')
format_subplot(ax_ut, (.9, .9), "e)",
               ticks=(None, [0, 1, 2]),
               lims=(None, [-0.1, 2.6]),
               ax_lbls=(x_label, y_label_utilisation))

ax_ut_PV.plot(data["m6PV"]["x_value"], data["m6PV"]["utilisation"],
              label="m6 Ut", linewidth=linewidth, color="k")
format_subplot(ax_ut_PV, (.9, .9), "f)",
               ticks=get_ticks(ax_ut),
               lims=get_lims(ax_ut),
               ax_lbls=(x_label, y_label_utilisation_apt))

plt.show()

file_name = "one_week_charge_ut_rev.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "one_week_charge_ut_rev.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)