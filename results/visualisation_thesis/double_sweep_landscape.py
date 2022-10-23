# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 14:00:30 2021

@author: S3739258
"""

import os
import fiona

from mpl_toolkits.mplot3d.axes3d import Axes3D
from mpl_toolkits.mplot3d import proj3d

import matplotlib.pyplot as plt
import matplotlib.patches
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable
matplotlib.rc('font', **{'sans-serif' : 'Arial',
                         'family' : 'sans-serif'})

import numpy as np
from matplotlib import cm
import matplotlib.gridspec as gridspec
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

from parameters import Parameters
from output_data import OutputData
from console_output import ConsoleOutput
from cast import Cast
from csv_helper import CSVHelper

###############################################################################
###############################################################################
##                                                                           ##
##                                 Constants                                 ##
##                                                                           ##
###############################################################################
###############################################################################

SINGLE_RUN = ["charge_received_time_series", "charger_utilisation_time_series",
              "location_time_series"]
D1_SWEEP = ["sweep_data"]
D2_SWEEP = ["avg_cost", "avg_cost_apartment", "avg_cost_house_no_pv",
            "avg_cost_house_pv", "charge_emergency", "charge_grid",
            "charge_held_back", "charge_pv", "charge_work", "utilisation"]
PATH = "results"

MY_DPI = 96
mpl.rcParams['figure.dpi'] = 300

file_m6_2d = "model_6_nbr_agents_2400_season_avg_avg_cost.csv"
file_m4_m6_2d = "model_4-6_nbr_agents_2400_season_avg-avg_-_diff_avg_cost.csv"
file_m4_1d = "model_4_nbr_agents_6000_season_avg_sweep_data.csv"
file_m6_1d = "model_6_nbr_agents_6000_season_avg_sweep_data.csv"
            
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

###############################################################################
###############################################################################
##                                                                           ##
##                               Read 2D Data                                ##
##                                                                           ##
###############################################################################
###############################################################################

cast = Cast("Analysis")

# remove rows from begin
rrb = 0
# remove rows from end
rre = -1
# focused rows
focus_rows = [-1,5,1]

first_row_m6_2d_org,  front_col_m6_2d,  data_m6_2d_org \
    = read_data(PATH, file_m6_2d)
first_row_m4_m6_2d_org, front_col_m4_m6_2d, data_m4_m6_2d_org \
    = read_data(PATH, file_m4_m6_2d)

first_row_m6_2d = first_row_m6_2d_org[rrb:rre]
first_row_m4_m6_2d = first_row_m4_m6_2d_org[rrb:rre]

data_m6_2d = []
for i, data_m6_2d_org_row in enumerate(data_m6_2d_org):
    row = []
    for j, data_m6_2d_org_val in enumerate(data_m6_2d_org_row[rrb:rre]):
        row.append(data_m6_2d_org_val * 10**2)
    data_m6_2d.append(row)
data_m4_m6_2d = []
for i, data_m4_m6_2d_org_row in enumerate(data_m4_m6_2d_org):
    row = []
    for j, data_m4_m6_2d_org_val in enumerate(data_m4_m6_2d_org_row[rrb:rre]):
        a = data_m6_2d_org[i][j]
        c = data_m4_m6_2d_org_val
        row.append(data_m4_m6_2d_org_val * 10**3)
        #row.append(a / (c+a))
    data_m4_m6_2d.append(row)
    
###############################################################################
###############################################################################
##                                                                           ##
##                               Read 1D Data                                ##
##                                                                           ##
###############################################################################
###############################################################################

names_1d = ["m4","m6"]
files_1d = [file_m4_1d, file_m6_1d]

data_1d = dict()
data_1d_diff = dict()
first_row_1d = dict()
front_col_1d = dict()
for it, name in enumerate(names_1d):
    first_row_1d[name], front_col_1d[name], data_tmp \
        = read_data(PATH, files_1d[it])
    data_1d[name] = dict()
    for it, first_row_cell in enumerate(first_row_1d[name]):
        if it == 0:
            data_1d[name]["x_value"] = front_col_1d[name]
        else:
            data_1d[name][first_row_cell] = []
            for data_row in data_tmp:
                data_1d[name][first_row_cell].append(data_row[it-1]*100)

###############################################################################
###############################################################################
##                                                                           ##
##                               Prepare Plots                               ##
##                                                                           ##
###############################################################################
###############################################################################

cmap = mpl.cm.viridis
x_label_m6_2d = "$p^w$ in \$/kWh"
x_label_m4_m6_2d = "$p^w$ in \$/kWh"
y_label_m6_2d = "$|I_j| / u_j$ in 1"
y_label_m4_m6_2d = "$|I_j| / u_j$ in 1"
y_label_m4_m6_1d = "$C_{\u2020,\u2217}$ in $10^{-2}$ \$/km"
z_label_m6_2d = "$C_{adv}$ in $10^{-2}$ \$/km"
z_label_m6_2d_two_lines = "$C_{\dagger}$ in $10^{-2}$ \$/km"
z_label_m4_m6_2d = "$C_{bsc} - C_{adv}$ in $10^{-3}$ \$/km"

x_ticks_m6_2d = [cast.to_float(i, "first_row_cell")\
                for i in first_row_m6_2d[1:]]
x_ticks_m4_m6_2d = [cast.to_float(i, "first_row_cell")\
                 for i in first_row_m4_m6_2d[1:]]
y_ticks_m6_2d = [cast.to_int(i, "front_col_cell") \
                for i in front_col_m6_2d]
y_ticks_m4_m6_2d = [cast.to_int(i, "front_col_cell") \
                 for i in front_col_m4_m6_2d]

linewidth = 1
cm = 1/2.54
fontsize=8

#margins
mt,mb, ml, mr = 0, 0, 0, 0
#horizontal center line
cl = .5
#horizontal space
hs = .1

fig = plt.figure(figsize=(14.65*cm, 9*cm))

gsMain = gridspec.GridSpec(1, 2, figure=fig, wspace=1.2*cm,
                        width_ratios=[.5,.5])
gsLeft = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gsMain[0],
                                          hspace=0)

ax_adv = fig.add_subplot(gsLeft[0, 0])
ax_bsc_adv = fig.add_subplot(gsLeft[1, 0])

"""
gsRight = gridspec.GridSpecFromSubplotSpec(len(focus_rows), 1,
                                           subplot_spec=gsMain[1], hspace=0)

ax_fr = []
for i, focus_row in enumerate(focus_rows):
    ax_fr.append(fig.add_subplot(gsRight[i, 0]))
"""

#ax_fr = fig.add_subplot(gsMain[0, 1])

gsRight = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gsMain[1],
                                          hspace=0)

# cost disaggregated by cost
ax_c_src = fig.add_subplot(gsRight[0, 0])
# cost versus employees per charger
ax_c_emp = fig.add_subplot(gsRight[1, 0], sharex=True)

###############################################################################
###############################################################################
##                                                                           ##
##                                Left Plots                                 ##
##                                                                           ##
###############################################################################
###############################################################################

vmin_m6_2d=min([min(row) for row in data_m6_2d])
vmin_m4_m6_2d=min([min(row) for row in data_m4_m6_2d])
vmax_m6_2d=max([max(row) for row in data_m6_2d])
vmax_m4_m6_2d=max([max(row) for row in data_m4_m6_2d])
norm_m6_2d = mpl.colors.Normalize(vmin=vmin_m6_2d, vmax=vmax_m6_2d)
norm_m4_m6_2d = mpl.colors.Normalize(vmin=vmin_m4_m6_2d, vmax=vmax_m4_m6_2d)
ax_adv.pcolormesh(x_ticks_m6_2d, y_ticks_m6_2d, data_m6_2d, cmap=cmap,
              shading='gouraud', vmin=vmin_m6_2d, vmax=vmax_m6_2d)
ax_adv.set_xlabel(x_label_m6_2d, fontsize=fontsize)
ax_adv.set_ylabel(y_label_m4_m6_2d, fontsize=fontsize)
ax_adv.minorticks_on()
ax_adv.tick_params(labelsize=fontsize)
ax_adv.xaxis.set_ticks_position('none')
ax_adv.xaxis.set_minor_locator(AutoMinorLocator())
ax_adv.set_xticklabels([])

divider = make_axes_locatable(ax_adv)
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm_m6_2d,cmap=cmap),
                    cax=cax)
cbar.minorticks_on()
cbar.ax.tick_params(labelsize=fontsize)
cbar.set_label(z_label_m6_2d, fontsize=fontsize)
ax_adv.text(.30, 4, "a)", va="bottom", ha="right", fontsize=fontsize)

ax_bsc_adv.pcolormesh(x_ticks_m4_m6_2d, y_ticks_m4_m6_2d, data_m4_m6_2d, cmap=cmap,
              shading='gouraud', vmin=vmin_m4_m6_2d, vmax=vmax_m4_m6_2d)
ax_bsc_adv.set_xlabel(x_label_m4_m6_2d, fontsize=fontsize)
ax_bsc_adv.set_ylabel(y_label_m4_m6_2d, fontsize=fontsize)
ax_bsc_adv.minorticks_on()
ax_bsc_adv.tick_params(labelsize=fontsize)
ax_bsc_adv.text(.30, 4, "b)", va="bottom", ha="right", fontsize=fontsize, color='w')

divider = make_axes_locatable(ax_bsc_adv)
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm_m4_m6_2d,cmap=cmap),
                    cax=cax)
cbar.minorticks_on()
cbar.ax.tick_params(labelsize=fontsize)
cbar.set_label(z_label_m4_m6_2d, fontsize=fontsize)

###############################################################################
###############################################################################
##                                                                           ##
##                                Right Plots                                ##
##                                                                           ##
###############################################################################
###############################################################################

ax_c_src

line1, = ax_c_src.plotx_ticks_m6_2d,
                       data_1d["m6"]["avg_cost_apartment"], label="m6 apt",
                       linewidth=linewidth, color="b")
ax_c_src.plotx_ticks_m6_2d, data_1d["m4"]["avg_cost_apartment"],
              label="m4 apt", linewidth=linewidth, color="b", linestyle='--')
line2, = ax_c_src.plot(data_1d["m6"]["x_value"],
                       data_1d["m6"]["avg_cost_house_no_pv"], label="m6 noPV",
                       linewidth=linewidth, color="r")
ax_c_src.plot(data_1d["m4"]["x_value"], data_1d["m4"]["avg_cost_house_no_pv"],
              label="m4 npPV", linewidth=linewidth, color="r", linestyle='--')
line3, = ax_c_src.plot(data_1d["m6"]["x_value"],
                       data_1d["m6"]["avg_cost_house_pv"], label="m6 PV",
                       linewidth=linewidth, color="g")
ax_c_src.plot(data_1d["m4"]["x_value"], data_1d["m4"]["avg_cost_house_pv"],
              label="m4 PV", linewidth=linewidth, color="g", linestyle='--')
ax_c_src.xaxis.set_ticks_position('none')
ax_c_src.xaxis.set_minor_locator(AutoMinorLocator())
ax_c_src.set_xticklabels([])
ax_c_src.set_ylabel(y_label_m4_m6_1d, fontsize=fontsize)
ax_c_src.yaxis.set_minor_locator(AutoMinorLocator())
ax_c_src.grid(True)
ax_c_src.tick_params(labelsize=fontsize)
ax_c_src.legend([line1, line2, line3],
                ['Apartment', 'House without PV', 'House with PV'],
                fontsize=fontsize, loc=2)
ax_c_src.text(.33, .4, "a)", va="bottom", ha="right", fontsize=fontsize)

clr_lns = ['k','r','b']

for i, focus_row in enumerate(focus_rows):
    data_adv = data_m6_2d[focus_row]
    data_bsc_sub_adv = data_m4_m6_2d[focus_row]
    data_bsc =[data_bsc_sub_adv[i] / 10 + data_adv[i] for i in range(len(data_adv))]
    data_abs = [data_bsc[i] - data_adv[i] for i in range(len(data_adv))]
    data_rel =[data_adv[i] / data_bsc[i] for i in range(len(data_adv))]
    
    """
    ax_fr[i].plot(x_ticks_m6_2d, data_adv, color='k')
    ax_fr[i].plot(x_ticks_m6_2d, data_bsc, color='k', linestyle='--')
    ax_fr[i].set_xlabel(x_label_m6_2d, fontsize=fontsize)
    ax_fr[i].set_ylabel(z_label_m6_2d_two_lines, fontsize=fontsize)
    ax_fr[i].minorticks_on()
    ax_fr[i].grid(True)
    ax_fr[i].tick_params(labelsize=fontsize)
    ax_fr[i].text(.32, 3.2, "c)", va="bottom", ha="right", fontsize=fontsize)
    """
    """
    ax_c_emp.plot(x_ticks_m6_2d, data_adv, color=clr_lns[i])
    ax_c_emp.plot(x_ticks_m6_2d, data_bsc, color=clr_lns[i], linestyle='dotted')
    """
    ax_c_emp.plot(x_ticks_m6_2d, data_bsc_sub_adv, color=clr_lns[i])
    #ax_fr.plot(x_ticks_m6_2d, data_bsc_sub_adv, color=clr_lns[i])
    
ax_c_emp.set_xlabel(x_label_m6_2d, fontsize=fontsize)
ax_c_emp.set_ylabel(z_label_m6_2d_two_lines, fontsize=fontsize)
ax_c_emp.minorticks_on()
ax_c_emp.grid(True)
ax_c_emp.tick_params(labelsize=fontsize)
# ax_fr.text(.3, .4, "c)", va="bottom", ha="right", fontsize=fontsize)

plt.show

file_name = "double_sweep.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "double_sweep.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)