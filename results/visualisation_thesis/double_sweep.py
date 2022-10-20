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

# remove rows from begin
rrb = 0
# remove rows from end
rre = -1
# focused rows
focus_rows = [-1,5,1]

first_row_left_org,  front_col_left,  data_left_org  = read_data(PATH, file_left)
first_row_right_org, front_col_right, data_right_org = read_data(PATH, file_right)

first_row_left = first_row_left_org[rrb:rre]
first_row_right = first_row_right_org[rrb:rre]

data_left = []
for i, data_left_org_row in enumerate(data_left_org):
    row = []
    for j, data_left_org_val in enumerate(data_left_org_row[rrb:rre]):
        row.append(data_left_org_val * 10**2)
    data_left.append(row)
data_right = []
for i, data_right_org_row in enumerate(data_right_org):
    row = []
    for j, data_right_org_val in enumerate(data_right_org_row[rrb:rre]):
        a = data_left_org[i][j]
        c = data_right_org_val
        #row.append(data_right_org_val * 10**3)
        row.append(a / (c+a))
    data_right.append(row)
    

cmap = mpl.cm.viridis
x_label_left = "$p^w$ in \$/kWh"
x_label_right = "$p^w$ in \$/kWh"
y_label_left = "$|I_j| / u_j$ in 1"
y_label_right = "$|I_j| / u_j$ in 1"
z_label_left = "$C_{adv}$ in $10^{-2}$ \$/km"
z_label_left_two_lines = "$C_{\dagger}$ in $10^{-2}$ \$/km"
z_label_right = "$C_{bsc} - C_{adv}$ in $10^{-3}$ \$/km"

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

ax_fr = fig.add_subplot(gsMain[0, 1])

vmin_left=min([min(row) for row in data_left])
vmin_right=min([min(row) for row in data_right])
vmax_left=max([max(row) for row in data_left])
vmax_right=max([max(row) for row in data_right])
norm_left = mpl.colors.Normalize(vmin=vmin_left, vmax=vmax_left)
norm_right = mpl.colors.Normalize(vmin=vmin_right, vmax=vmax_right)
ax_adv.pcolormesh(x_ticks_left, y_ticks_left, data_left, cmap=cmap,
              shading='gouraud', vmin=vmin_left, vmax=vmax_left)
ax_adv.set_xlabel(x_label_left, fontsize=fontsize)
ax_adv.set_ylabel(y_label_right, fontsize=fontsize)
ax_adv.minorticks_on()
ax_adv.tick_params(labelsize=fontsize)
ax_adv.xaxis.set_ticks_position('none')
ax_adv.xaxis.set_minor_locator(AutoMinorLocator())
ax_adv.set_xticklabels([])

divider = make_axes_locatable(ax_adv)
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm_left,cmap=cmap),
                    cax=cax)
cbar.minorticks_on()
cbar.ax.tick_params(labelsize=fontsize)
cbar.set_label(z_label_left, fontsize=fontsize)
ax_adv.text(.30, 4, "a)", va="bottom", ha="right", fontsize=fontsize)

ax_bsc_adv.pcolormesh(x_ticks_right, y_ticks_right, data_right, cmap=cmap,
              shading='gouraud', vmin=vmin_right, vmax=vmax_right)
ax_bsc_adv.set_xlabel(x_label_right, fontsize=fontsize)
ax_bsc_adv.set_ylabel(y_label_right, fontsize=fontsize)
ax_bsc_adv.minorticks_on()
ax_bsc_adv.tick_params(labelsize=fontsize)
ax_bsc_adv.text(.30, 4, "b)", va="bottom", ha="right", fontsize=fontsize, color='w')

divider = make_axes_locatable(ax_bsc_adv)
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm_right,cmap=cmap),
                    cax=cax)
cbar.minorticks_on()
cbar.ax.tick_params(labelsize=fontsize)
cbar.set_label(z_label_right, fontsize=fontsize)

clr_lns = ['k','r','b']

for i, focus_row in enumerate(focus_rows):
    data_adv = data_left[focus_row]
    data_bsc_sub_adv = data_right[focus_row]
    data_bsc =[data_bsc_sub_adv[i] / 10 + data_adv[i] for i in range(len(data_adv))]
    data_rel =[data_adv[i] / data_bsc[i] for i in range(len(data_adv))]
    
    """
    ax_fr[i].plot(x_ticks_left, data_adv, color='k')
    ax_fr[i].plot(x_ticks_left, data_bsc, color='k', linestyle='--')
    ax_fr[i].set_xlabel(x_label_left, fontsize=fontsize)
    ax_fr[i].set_ylabel(z_label_left_two_lines, fontsize=fontsize)
    ax_fr[i].minorticks_on()
    ax_fr[i].grid(True)
    ax_fr[i].tick_params(labelsize=fontsize)
    ax_fr[i].text(.32, 3.2, "c)", va="bottom", ha="right", fontsize=fontsize)
    """
    """
    ax_fr.plot(x_ticks_left, data_adv, color=clr_lns[i])
    ax_fr.plot(x_ticks_left, data_bsc, color=clr_lns[i], linestyle='dotted')
    """
    ax_fr.plot(x_ticks_left, data_bsc_sub_adv, color=clr_lns[i])
    
ax_fr.set_xlabel(x_label_left, fontsize=fontsize)
ax_fr.set_ylabel(z_label_left_two_lines, fontsize=fontsize)
ax_fr.minorticks_on()
ax_fr.grid(True)
ax_fr.tick_params(labelsize=fontsize)
# ax_fr.text(.3, .4, "c)", va="bottom", ha="right", fontsize=fontsize)

plt.show

file_name = "double_sweep.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "double_sweep.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)