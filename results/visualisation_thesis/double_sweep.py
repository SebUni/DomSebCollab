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

fig_lbl = iter(["a)", "b)", "c)", "d)", "e)", "h)", "g)", "f)", "i)"])

file_m6_2d = "model_8_nbr_agents_6k_season_avg_avg_cost.csv"
file_m4_m6_2d = "model_9-8_nbr_agents_6k_season_avg-avg_-_diff_avg_cost.csv"
file_m4_m6_2d_apt \
    = "model_9-8_nbr_agents_6k_season_avg-avg_-_diff_avg_cost_apartment.csv"
file_m4_m6_2d_hNPV \
    = "model_9-8_nbr_agents_6k_season_avg-avg_-_diff_avg_cost_house_no_pv.csv"
file_m4_m6_2d_hPV \
    = "model_9-8_nbr_agents_6k_season_avg-avg_-_diff_avg_cost_house_PV.csv"
file_m4_a = "model_9_nbr_agents_6k_season_avg_avg_cost_apartment.csv"
file_m4_wo = "model_9_nbr_agents_6k_season_avg_avg_cost_house_no_pv.csv"
file_m4_w = "model_9_nbr_agents_6k_season_avg_avg_cost_house_pv.csv"
file_m6_a = "model_8_nbr_agents_6k_season_avg_avg_cost_apartment.csv"
file_m6_wo = "model_8_nbr_agents_6k_season_avg_avg_cost_house_no_pv.csv"
file_m6_w = "model_8_nbr_agents_6k_season_avg_avg_cost_house_pv.csv"
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
focus_rows = [0,6,-1]

file_m4_m6_2d_apt, file_m4_m6_2d_hNPV, file_m4_m6_2d_hPV

names_2d = ["m6", "m4-6", "m4-6a", "m4-6wo", "m4-6w", "m4a", "m4wo", "m4w", 
            "m6a", "m6wo", "m6w"]
files_2d = [file_m6_2d, file_m4_m6_2d, file_m4_m6_2d_apt, file_m4_m6_2d_hNPV,
            file_m4_m6_2d_hPV, file_m4_a, file_m4_wo, file_m4_w, file_m6_a,
            file_m6_wo, file_m6_w]
scales = [10**2, 10**3] + [10**3, 10**3, 10**2] + [10**2]*6

plots_2d = ["m6", "m4-6", "m4-6a", "m4-6wo", "m4-6w"]

data_2d = dict()
first_row_2d = dict()
front_col_2d = dict()
for name_2d, file_2d, scale in zip(names_2d, files_2d, scales):
    first_row_tmp, front_col_2d[name_2d], data_tmp \
        = read_data(PATH, file_2d)
    
    first_row_2d[name_2d] = first_row_tmp
    data_2d[name_2d] = [[c * scale for c in r] for r in data_tmp]
    
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
x_label = "$p^w$ in \$/kWh"
y_label = {"m6": "$|I_j| / u_j$ in 10",
           "m4+6": "$C_{\u2020,\u2217}$ in $10^{-2}$ \$/km",
           "m4+6_avg": "$C_{\dagger}$ in $10^{-2}$ \$/km"}
z_label = {"m6": "$C_{adv}$ in $10^{-2}$ \$/km",
           "m4-6": "$C_{bsc} - C_{adv}$ in $10^{-3}$ \$/km",
           "m4-6a": "$C_{bsc,apt} - C_{adv,apt}$ \n in $10^{-3}$ \$/km",
           "m4-6wo": "$C_{bsc,h} - C_{adv,h}$ \n in $10^{-3}$ \$/km",
           "m4-6w": "$C_{bsc,hPV} - C_{adv,hPV}$ \n in $10^{-3}$ \$/km"}
z_ticks = {"m6": None,
           "m4-6": None,
           "m4-6a": [0,3,6],
           "m4-6wo": None,
           "m4-6w": None}

x_ticks_2d = [cast.to_float(i, "first_row_cell")\
                for i in first_row_2d["m6"][1:]]
y_ticks_2d = [cast.to_int(i, "front_col_cell") / 10 \
                for i in front_col_2d["m6"]]

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

fig = plt.figure(figsize=(15.5*cm, 20*cm))

gsMain = gridspec.GridSpec(1, 2, figure=fig, wspace=1.6*cm,
                        width_ratios=[.48,.52,])

gsLeft = gridspec.GridSpecFromSubplotSpec(5, 1, subplot_spec=gsMain[0],
                                          hspace=0,
                                          height_ratios=[25,25,16.7,16.7,16.6])

gsRight = gridspec.GridSpecFromSubplotSpec(len(focus_rows)+1, 1,
                                           subplot_spec=gsMain[1],
                                           wspace=1.5*cm, hspace=0,
                                           height_ratios=[250,175,175,400])

ax_l = {"m6": fig.add_subplot(gsLeft[0, 0]),
        "m4-6": fig.add_subplot(gsLeft[1, 0]),
        "m4-6a": fig.add_subplot(gsLeft[2, 0]),
        "m4-6wo": fig.add_subplot(gsLeft[3, 0]),
        "m4-6w": fig.add_subplot(gsLeft[4, 0])}
# ax_rel = fig.add_subplot(gsLeft[2, 0])

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

vmin = dict([(key, min([min(row) for row in data_2d[key]]))
             for key in plots_2d])
vmax = dict([(key, max([max(row) for row in data_2d[key]]))
             for key in plots_2d])
norm = dict([(key, mpl.colors.Normalize(vmin=vmin[key], vmax=vmax[key]))
             for key in plots_2d])

lbl_clr = {"m6": 'k',
           "m4-6": 'w',
           "m4-6a": 'w',
           "m4-6wo": 'w',
           "m4-6w": 'k'}

for k in plots_2d:
    ax_l[k].pcolormesh(x_ticks_2d, y_ticks_2d, data_2d[k], cmap=cmap,
                       shading='gouraud', vmin=vmin[k], vmax=vmax[k])
    ax_l[k].set_ylabel(y_label["m6"], fontsize=fontsize)
    ax_l[k].minorticks_on()
    ax_l[k].tick_params(labelsize=fontsize)
    ax_l[k].xaxis.set_minor_locator(AutoMinorLocator())
    ax_l[k].yaxis.set_minor_locator(AutoMinorLocator())
    ax_l[k].set_yticks([2,4,6,8])
    if plots_2d[-1] != k:
        ax_l[k].xaxis.set_ticks_position('none')
        ax_l[k].set_xticklabels([])
    ax_l[k].text(*lbl_abs_pos(ax_l[k], (0.9, 0.96)), next(fig_lbl), va="top",
                 ha="left", fontsize=fontsize, color=lbl_clr[k])
    
    divider = make_axes_locatable(ax_l[k])
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm[k],cmap=cmap), cax=cax)
    if z_ticks[k] is not None:
        cbar.set_ticks(z_ticks[k])
    cbar.minorticks_on()
    cbar.ax.tick_params(labelsize=fontsize)
    cbar.set_label(z_label[k], fontsize=fontsize)

# Rel plot

"""
clr_lns = ['k','r','b']

ln_c_rel = dict()

for focus_row, clr_ln in zip(focus_rows, clr_lns):
    data_adv = data_2d["m6"][focus_row]
    data_bsc_sub_adv = data_2d["m4-6"][focus_row]
    data_bsc = [dba / 10 + da for dba, da in zip(data_bsc_sub_adv, data_adv)]
    data_abs = [db - da for db, da in zip(data_bsc, data_adv)]
    data_rel = [da * 100 / db for db, da in zip(data_bsc, data_adv)]
    
    # Plot lines
    
    ln_sld, = ax_rel.plot(x_ticks_m6_2d, data_rel, color=clr_ln)
    ln_c_rel["|$I_j$|/$u_j$ = " + front_col_2d["m6"][focus_row]] = ln_sld

# Style plot
ax_rel.set_xlabel(x_label_m6_2d, fontsize=fontsize)
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
"""

ax_l[plots_2d[-1]].set_xlabel(x_label, fontsize=fontsize)

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
    ax_c_dwl[fr].set_ylabel(y_label["m4+6"], fontsize=fontsize)
    ax_c_dwl[fr].yaxis.set_minor_locator(AutoMinorLocator())
    ax_c_dwl[fr].grid(True)
    ax_c_dwl[fr].tick_params(labelsize=fontsize)
    
    fig_lbl_pos = (0.05, 0.94)
    if fr == focus_rows[-1]:
        ylim = ax_c_dwl[fr].get_ylim()
        ax_c_dwl[fr].set_ylim((ylim[0], ylim[1] + (ylim[1] - ylim[0]) * .6))
        ax_c_dwl[fr].legend([line1, line2, line3], 
                            ["Apartment (apt)","House without PV (h)",
                             "House with PV (hPV)"],
                            fontsize=fontsize, loc=2)
        fig_lbl_pos = (0.9, 0.94)
    ax_c_dwl[fr].text(*lbl_abs_pos(ax_c_dwl[fr], fig_lbl_pos), next(fig_lbl),
                      va="top", ha="left", fontsize=fontsize)

# Bottom Plot
for focus_row, clr_ln in zip(focus_rows, clr_lns):
    data_adv = data_2d["m6"][focus_row]
    data_bsc_sub_adv = data_2d["m4-6"][focus_row]
    data_bsc = [dba / 10 + da for dba, da in zip(data_bsc_sub_adv, data_adv)]
    data_abs = [db - da for db, da in zip(data_bsc, data_adv)]
    data_rel = [db / da for db, da in zip(data_bsc, data_adv)]
    
    # Plot lines
    ln_sld, = ax_c_emp.plot(x_ticks_2d, data_adv, color=clr_ln)
    ln_c_emp_sld["|$I_j$|/$u_j$ = " + front_col_2d["m6"][focus_row]] = ln_sld
        
    ln_dsh, = ax_c_emp.plot(x_ticks_2d, data_bsc, color=clr_ln,
                        linestyle='dotted')
    ln_c_emp_dsh["|$I_j$|/$u_j$ = " + front_col_2d["m6"][focus_row]] = ln_dsh
    
    if clr_ln == "k":
        ln_c_emp_sld_k = ln_sld
        ln_c_emp_dsh_k = ln_dsh
        
    #ax_c_emp.plot(x_ticks_m6_2d, data_bsc_sub_adv, color=clr_lns[i])
    #ax_fr.plot(x_ticks_m6_2d, data_bsc_sub_adv, color=clr_lns[i])

# Style plot
ax_c_emp.set_xlabel(x_label, fontsize=fontsize)
ax_c_emp.set_ylabel(y_label["m4+6_avg"], fontsize=fontsize)
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