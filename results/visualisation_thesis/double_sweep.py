# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 14:00:30 2021

@author: S3739258
"""

import matplotlib.pyplot as plt
import matplotlib.patches
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable
matplotlib.rc('font', **{'sans-serif' : 'Arial',
                         'family' : 'sans-serif'})

import matplotlib.gridspec as gridspec
from matplotlib.ticker import AutoMinorLocator

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

fig_lbl = iter(["a)", "b)", "c)", "f)", "e)", "d)", "g)"])

file_m6_2d = "model_8_nbr_agents_2400_season_avg_avg_cost.csv"
file_m4_m6_2d = "model_9-8_nbr_agents_2400_season_avg-avg_-_diff_avg_cost.csv"
file_m4_a = "model_9_nbr_agents_2400_season_avg_avg_cost_apartment.csv"
file_m4_wo = "model_9_nbr_agents_2400_season_avg_avg_cost_house_no_pv.csv"
file_m4_w = "model_9_nbr_agents_2400_season_avg_avg_cost_house_pv.csv"
file_m6_a = "model_8_nbr_agents_2400_season_avg_avg_cost_apartment.csv"
file_m6_wo = "model_8_nbr_agents_2400_season_avg_avg_cost_house_no_pv.csv"
file_m6_w = "model_8_nbr_agents_2400_season_avg_avg_cost_house_pv.csv"
file_m4_1d = "model_9_nbr_agents_6000_season_avg_sweep_data.csv"
file_m6_1d = "model_8_nbr_agents_6000_season_avg_sweep_data.csv"
            
def read_data(relative_path, file_name):
    cast = Cast("difference_tool")
    csv_helper = CSVHelper(relative_path, file_name, skip_header=False)
    first_row = csv_helper.data[0]
    front_col, data = [], []
    for row in csv_helper.data[1:]:
        front_col.append(row[0])
        data.append([cast.to_float(cell, "data_cell") for cell in row[1:]])
    return first_row, front_col, data

def lbl_abs_pos(axes: mpl.axes, rel_pos: tuple):
    lim = (axes.get_xlim(), axes.get_ylim())
    return (l[0] + (l[1] - l[0]) * r for l, r in zip(lim, rel_pos))

###############################################################################
###############################################################################
##                                                                           ##
##                               Read 2D Data                                ##
##                                                                           ##
###############################################################################
###############################################################################

cast = Cast("Analysis")

# focused rows
focus_rows = [0,5,-1]

first_row_m6_2d_org,  front_col_m6_2d,  data_m6_2d_org \
    = read_data(PATH, file_m6_2d)
first_row_m4_m6_2d_org, front_col_m4_m6_2d, data_m4_m6_2d_org \
    = read_data(PATH, file_m4_m6_2d)

first_row_m6_2d = first_row_m6_2d_org
first_row_m4_m6_2d = first_row_m4_m6_2d_org

data_m6_2d = []
for i, data_m6_2d_org_row in enumerate(data_m6_2d_org):
    row = []
    for j, data_m6_2d_org_val in enumerate(data_m6_2d_org_row):
        row.append(data_m6_2d_org_val * 10**2)
    data_m6_2d.append(row)
data_m4_m6_2d = []
for i, data_m4_m6_2d_org_row in enumerate(data_m4_m6_2d_org):
    row = []
    for j, data_m4_m6_2d_org_val in enumerate(data_m4_m6_2d_org_row):
        a = data_m6_2d_org[i][j]
        c = data_m4_m6_2d_org_val
        row.append(data_m4_m6_2d_org_val * 10**3)
        #row.append(a / (c+a))
    data_m4_m6_2d.append(row)
    
names_2d = ["m4a","m4wo","m4w","m6a","m6wo","m6w"]
files_2d = [file_m4_a, file_m4_wo, file_m4_w,
            file_m6_a, file_m6_wo, file_m6_w]

data_2d = dict()
first_row_2d = dict()
front_col_2d = dict()
for name_2d, file_2d in zip(names_2d, files_2d):
    first_row_tmp, front_col_2d[name_2d], data_tmp \
        = read_data(PATH, file_2d)
    
    first_row_2d[name_2d] = first_row_tmp
    data_2d[name_2d] = [[c * 10**2 for c in r] for r in data_tmp]
    
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
for name, file in zip(names_1d, files_1d):
    first_row_1d[name], front_col_tmp, data_tmp \
        = read_data(PATH, file)
    front_col_1d[name] = front_col_tmp
    data_1d[name] = dict()
    data_1d[name]["x_value"] = [float(x) for x in front_col_1d[name]]
    for it, first_row_cell in enumerate(first_row_1d[name][:-1]):
        data_1d[name][first_row_cell] = []
        for data_row in data_tmp:
            data_1d[name][first_row_cell].append(data_row[it]*100)

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
y_label_rel = "$C_{adv}/C_{bsc}$ in %"
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
fontsize = 8
fontsize_leg = 4

#margins
mt,mb, ml, mr = 0, 0, 0, 0
#horizontal center line
cl = .5
#horizontal space
hs = .1

fig = plt.figure(figsize=(14.5*cm, 20*cm))

gsMain = gridspec.GridSpec(1, 2, figure=fig, wspace=1.3*cm,
                        width_ratios=[.5,.5,])

gsLeft = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=gsMain[0],
                                          hspace=0,
                                          height_ratios=[30,30,40])

gsRight = gridspec.GridSpecFromSubplotSpec(len(focus_rows)+1, 1,
                                           subplot_spec=gsMain[1],
                                           wspace=1.5*cm, hspace=0,
                                           height_ratios=[250,175,175,400])

ax_adv = fig.add_subplot(gsLeft[0, 0])
ax_bsc_adv = fig.add_subplot(gsLeft[1, 0])
ax_rel = fig.add_subplot(gsLeft[2, 0])

"""
gsRight = gridspec.GridSpecFromSubplotSpec(len(focus_rows), 1,
                                           subplot_spec=gsMain[1], hspace=0)

ax_fr = []
for i, focus_row in enumerate(focus_rows):
    ax_fr.append(fig.add_subplot(gsRight[i, 0]))
"""

ax_c_emp = fig.add_subplot(gsRight[len(focus_rows), 0])
ax_c_dwl = dict()
for i in range(len(focus_rows)):
    ax_c_dwl[focus_rows[i]] = fig.add_subplot(gsRight[len(focus_rows)-i-1, 0])

"""
gsRight = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gsMain[1],
                                          hspace=0)

# cost disaggregated by cost
ax_c_src = fig.add_subplot(gsRight[0, 0])
# cost versus employees per charger
ax_c_emp = fig.add_subplot(gsRight[1, 0], sharex=ax_c_src)
"""

###############################################################################
###############################################################################
##                                                                           ##
##                                Left Plots                                 ##
##                                                                           ##
###############################################################################
###############################################################################

# Surface plots

vmin_m6_2d=min([min(row) for row in data_m6_2d])
vmin_m4_m6_2d=min([min(row) for row in data_m4_m6_2d])
vmax_m6_2d=max([max(row) for row in data_m6_2d])
vmax_m4_m6_2d=max([max(row) for row in data_m4_m6_2d])
norm_m6_2d = mpl.colors.Normalize(vmin=vmin_m6_2d, vmax=vmax_m6_2d)
norm_m4_m6_2d = mpl.colors.Normalize(vmin=vmin_m4_m6_2d, vmax=vmax_m4_m6_2d)

for ax, xticks, yticks, data, vmin, vmax, norm, ylabel, zlabel, c \
    in zip((ax_adv, ax_bsc_adv), (x_ticks_m6_2d, x_ticks_m4_m6_2d),
           (y_ticks_m6_2d, y_ticks_m4_m6_2d), (data_m6_2d, data_m4_m6_2d),
           (vmin_m6_2d, vmin_m4_m6_2d), (vmax_m6_2d, vmax_m4_m6_2d),
           (norm_m6_2d, norm_m4_m6_2d), (y_label_m4_m6_2d, y_label_m4_m6_2d),
           (z_label_m6_2d, z_label_m4_m6_2d), ('k', 'w')):
    ax.pcolormesh(xticks, yticks, data, cmap=cmap, shading='gouraud',
                  vmin=vmin, vmax=vmax)
    ax.set_ylabel(ylabel, fontsize=fontsize)
    ax.minorticks_on()
    ax.tick_params(labelsize=fontsize)
    ax.xaxis.set_ticks_position('none')
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xticklabels([])
    ax.text(*lbl_abs_pos(ax, (0.9, 0.96)), next(fig_lbl), va="top", ha="left",
            fontsize=fontsize, color=c)
    
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap), cax=cax)
    cbar.minorticks_on()
    cbar.ax.tick_params(labelsize=fontsize)
    cbar.set_label(zlabel, fontsize=fontsize)

# Rel plot

clr_lns = ['k','r','b']

ln_c_rel = dict()

for focus_row, clr_ln in zip(focus_rows, clr_lns):
    data_adv = data_m6_2d[focus_row]
    data_bsc_sub_adv = data_m4_m6_2d[focus_row]
    data_bsc = [dba / 10 + da for dba, da in zip(data_bsc_sub_adv, data_adv)]
    data_abs = [db - da for db, da in zip(data_bsc, data_adv)]
    data_rel = [da * 100 / db for db, da in zip(data_bsc, data_adv)]
    
    # Plot lines
    
    ln_sld, = ax_rel.plot(x_ticks_m6_2d, data_rel, color=clr_ln)
    ln_c_rel["|$I_j$|/$u_j$ = " + front_col_m6_2d[focus_row]] = ln_sld

# Style plot
ax_rel.set_xlabel(x_label_m6_2d, fontsize=fontsize)
ax_rel.set_ylabel(y_label_rel, fontsize=fontsize)
ylim = ax_rel.get_ylim()
ax_rel.set_ylim((ylim[0], ylim[1] + (ylim[1] - ylim[0]) * .1))
ax_rel.minorticks_on()
ax_rel.grid(True)
ax_rel.tick_params(labelsize=fontsize)
ax_rel.legend(ln_c_rel.values(), ln_c_rel.keys(),
              fontsize=fontsize, loc=1)
ax_rel.text(*lbl_abs_pos(ax_rel, (0.05, 0.97)), next(fig_lbl), va="top",
            ha="left", fontsize=fontsize)
# ax_fr.text(.3, .4, "c)", va="bottom", ha="right", fontsize=fontsize)

###############################################################################
###############################################################################
##                                                                           ##
##                                Right Plot                                 ##
##                                                                           ##
###############################################################################
###############################################################################

# Focus Row Plots

clr_lns = ['k','r','b']

ln_c_emp_sld = dict()
ln_c_emp_dsh = dict()
ln_c_emp_sld_k = ""
ln_c_emp_dsh_k = ""

for fr in focus_rows:
    # Plot lines
    line1, = ax_c_dwl[fr].plot(data_1d["m4"]["x_value"],
                               data_2d["m6a"][fr], label="m6 apt",
                               color="orange")
    ax_c_dwl[fr].plot(data_1d["m4"]["x_value"], data_2d["m4a"][fr],
                      label="m4 apt", color="orange", linestyle='dotted')
    line2, = ax_c_dwl[fr].plot(data_1d["m6"]["x_value"],
                               data_2d["m6wo"][fr], label="m6 noPV",
                               color="g")
    ax_c_dwl[fr].plot(data_1d["m4"]["x_value"], data_2d["m4wo"][fr],
                      label="m4 npPV", color="g", linestyle='dotted')
    line3, = ax_c_dwl[fr].plot(data_1d["m6"]["x_value"],
                               data_2d["m6w"][fr], label="m6 PV",
                               color="m")
    line3d, = ax_c_dwl[fr].plot(data_1d["m4"]["x_value"], data_2d["m4w"][fr],
                                label="m4 PV", color="m", linestyle='dotted')
    # Style plot
    ax_c_dwl[fr].minorticks_on()
    ax_c_dwl[fr].xaxis.set_ticks_position('none')
    ax_c_dwl[fr].xaxis.set_minor_locator(AutoMinorLocator())
    ax_c_dwl[fr].set_xticklabels([])
    ax_c_dwl[fr].set_ylabel(y_label_m4_m6_1d, fontsize=fontsize)
    ax_c_dwl[fr].yaxis.set_minor_locator(AutoMinorLocator())
    ax_c_dwl[fr].grid(True)
    ax_c_dwl[fr].tick_params(labelsize=fontsize)
    
    fig_lbl_pos = (0.05, 0.94)
    if fr == focus_rows[-1]:
        ylim = ax_c_dwl[fr].get_ylim()
        ax_c_dwl[fr].set_ylim((ylim[0], ylim[1] + (ylim[1] - ylim[0]) * .6))
        ax_c_dwl[fr].legend([line1, line2, line3], 
                            ["Apartment","House without PV","House with PV"],
                            fontsize=fontsize, loc=2)
        fig_lbl_pos = (0.9, 0.94)
    ax_c_dwl[fr].text(*lbl_abs_pos(ax_c_dwl[fr], fig_lbl_pos), next(fig_lbl),
                      va="top", ha="left", fontsize=fontsize)

# Bottom Plot
for focus_row, clr_ln in zip(focus_rows, clr_lns):
    data_adv = data_m6_2d[focus_row]
    data_bsc_sub_adv = data_m4_m6_2d[focus_row]
    data_bsc = [dba / 10 + da for dba, da in zip(data_bsc_sub_adv, data_adv)]
    data_abs = [db - da for db, da in zip(data_bsc, data_adv)]
    data_rel = [db / da for db, da in zip(data_bsc, data_adv)]
    
    # Plot lines
    ln_sld, = ax_c_emp.plot(x_ticks_m6_2d, data_adv, color=clr_ln)
    ln_c_emp_sld["|$I_j$|/$u_j$ = " + front_col_m6_2d[focus_row]] = ln_sld
        
    ln_dsh, = ax_c_emp.plot(x_ticks_m6_2d, data_bsc, color=clr_ln,
                        linestyle='dotted')
    ln_c_emp_dsh["|$I_j$|/$u_j$ = " + front_col_m6_2d[focus_row]] = ln_dsh
    
    if clr_ln == "k":
        ln_c_emp_sld_k = ln_sld
        ln_c_emp_dsh_k = ln_dsh
        
    #ax_c_emp.plot(x_ticks_m6_2d, data_bsc_sub_adv, color=clr_lns[i])
    #ax_fr.plot(x_ticks_m6_2d, data_bsc_sub_adv, color=clr_lns[i])

# Style plot
ax_c_emp.set_xlabel(x_label_m6_2d, fontsize=fontsize)
ax_c_emp.set_ylabel(z_label_m6_2d_two_lines, fontsize=fontsize)
ax_c_emp.minorticks_on()
ax_c_emp.grid(True)
ax_c_emp.tick_params(labelsize=fontsize)

leg0 = ax_c_emp.legend([ln_c_emp_sld_k, ln_c_emp_dsh_k], ["adv", "bsc"],
                       fontsize=fontsize, loc=2)
leg1 = ax_c_emp.legend(ln_c_emp_sld.values(), ln_c_emp_sld.keys(),
                       fontsize=fontsize, loc=4)
ax_c_emp.add_artist(leg0)
ax_c_emp.text(*lbl_abs_pos(ax_c_emp, (0.9, 0.97)), next(fig_lbl), va="top",
              ha="left", fontsize=fontsize)

plt.show

file_name = "double_sweep.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "double_sweep.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)