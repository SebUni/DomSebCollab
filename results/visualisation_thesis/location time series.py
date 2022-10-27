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
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

import numpy as np

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

# moving average over maw time steps
maw = 12

# charge recieved by source
file_source = "model_10-8_nbr_agents_12000_26c_season_avg-avg_-_diff_charge_received_time_series.csv"
# charge received by location
file_location = "model_10-8_nbr_agents_12000_26c_season_avg-avg_-_diff_location_time_series.csv"

names = ["source","location"]
files = [file_source, file_location]

###############################################################################
###############################################################################
##                                                                           ##
##                         Read and Pre-Process Data                         ##
##                                                                           ##
###############################################################################
###############################################################################
            
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
            data.append([-cast.to_float(cell, "data_cell") for cell in row[1:]])
    return first_row, front_col, data

def get_color(cmap, value, min_value, max_value):
    _max = max(abs(min_value), max_value)
    rel_value = 0.5 + value / _max
    return list(cmap(rel_value))[:3]
    if rel_value <= 0:
        return [1+rel_value,1+rel_value,1]
    else:
        return [1,1-rel_value,1-rel_value]

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
                if name == "location":
                    data_raw[name][first_row_cell].append(-data_row[it-1]*12*100/10**6)
                else:
                    data_raw[name][first_row_cell].append(data_row[it-1]*12*100/10**6)

# add sum for locations
data_raw["location"]["summ"] = []
for it in range(0,len(data_raw["location"]["x_value"])):
    summ = 0
    for name, row in data_raw["location"].items():
        if name != "x_value" and name != "summ":
            summ += row[it]
    data_raw["location"]["summ"].append(summ / 10)
    
location_sum = dict()
for name, data_set in data_raw["location"].items():
    if name != "summ" and name != "x_value":
        location_sum[name] = sum(data_set) / 12
   
###############################################################################
###############################################################################
##                                                                           ##
##                         Calculate Moving Average                          ##
##                                                                           ##
###############################################################################
###############################################################################
data_maw = dict()
for name, data_set in data_raw.items():
    data_maw[name] = dict()
    for col_name, col_data in data_set.items():
        if col_name == "x_value":
            data_maw[name][col_name] = col_data
        else:
            data_maw[name][col_name] = []
            for it, value in enumerate(col_data):
                start_it = it - maw // 2
                end_it = start_it + maw
                _sum = 0
                for i in range(0, maw):
                    _sum += col_data[(start_it + i) % len(col_data)]
                avg_value = _sum / maw
                data_maw[name][col_name].append(avg_value)

demand_VIC = []
demand_VIC_time_step = np.arange(0,168,.5)
cast = Cast("demand VIC")
csv_helper = CSVHelper("results", "demand_VIC.csv", skip_header=True)
for row in csv_helper.data:
    demand_VIC.append(cast.to_float(row[2],"demand"))
# min_value = min(demand_VIC)
# demand_VIC = [value - min_value for value in demand_VIC]
demand_VIC = [value / 1000 for value in demand_VIC]
demand_VIC_adp = [dVIC + 10
                  * sum([data_maw["location"]["summ"]
                         [(i * 6 + j) % len(data_maw["location"]["summ"])]
                         for j in range(6)]) / 6
                  for i, dVIC in enumerate(demand_VIC)]

cast = Cast("Analysis")

###############################################################################
###############################################################################
##                                                                           ##
##                               Set Up Layout                               ##
##                                                                           ##
###############################################################################
###############################################################################

x_label = "$t$ in h"

linewidth = 1
linewidth_map = 0.3
cm = 1/2.54
fontsize = 8
fontsize_leg = 4

fig = plt.figure(figsize=(14.65*cm, 20.5*cm))

gsMain = gridspec.GridSpec(2, 1, figure=fig, hspace=.3*cm,
                           height_ratios=[50, 50])
gsTop = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=gsMain[0],
                                         wspace=0, width_ratios=[10, 65, 25])
gsMidBot = gridspec.GridSpecFromSubplotSpec(2, 2, subplot_spec=gsMain[1],
                                           hspace=0*cm,wspace=0,
                                           height_ratios=[40, 60],
                                           width_ratios=[75, 25])
gsBotAx = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gsMidBot[2],
                                           hspace=.2*cm,
                                           height_ratios=[50, 50])

ax_source = fig.add_subplot(gsMidBot[0, 0])
ax_locations = [0, 1]
ax_locations[1] = fig.add_subplot(gsBotAx[1, 0])
ax_locations[0] = fig.add_subplot(gsBotAx[0, 0])
ax_map = fig.add_subplot(gsTop[0, 1])
ax_hide = fig.add_subplot(gsTop[0, 2])

ax_hide.axis('off')

###############################################################################
###############################################################################
##                                                                           ##
##                          Difference Source Plot                           ##
##                                                                           ##
###############################################################################
###############################################################################

ds = data_maw["source"]
ax_source.plot(ds["x_value"], ds["charge_received_grid"], label="Grid",
               linewidth=linewidth, color='k')
ax_source.plot(ds["x_value"], ds["charge_received_pv"], label="PV",
               linewidth=linewidth, color='g')
ax_source.plot(ds["x_value"], ds["charge_received_work"], label="Work",
               linewidth=linewidth, color='r')
ax_source.plot(ds["x_value"], ds["charge_received_public"], label="Public",
               linewidth=linewidth, color='b')
ax_source.xaxis.set_minor_locator(AutoMinorLocator())
ax_source.set_xticks(range(0, 24*8, 24))
ax_source.set_xlim(0,168)
ax_source.yaxis.set_minor_locator(AutoMinorLocator())
ax_source.tick_params(labelsize=fontsize)
ax_source.grid(True)

# Remove Bottom Axis Clutter
ax_source.xaxis.set_ticks_position('none')
ax_source.set_xticklabels([])

# set labels
ax_source.set_xlabel(x_label, fontsize=fontsize)
ax_source.text(-20, sum(ax_source.get_ylim()) / 2,
               "$P_{adv,\u26AA} - P_{nw,\u26AA}$ in GW", va="center",
               ha="center", rotation="vertical", fontsize=fontsize)
# set legend
ax_source.legend(fontsize=fontsize,loc="center right",
                 bbox_to_anchor=(1.35, .5))
ax_source.text(164, -0.9, "b)", va="bottom", ha="right", fontsize=fontsize)

###############################################################################
###############################################################################
##                                                                           ##
##                         Difference Location Plot                          ##
##                                                                           ##
###############################################################################
###############################################################################

dl = data_maw["location"]
ln_loc_tot, ln_loc_206, ln_loc_212,  ln_loc_dVIC, ln_loc_dAdp = 0, 0, 0, 0, 0
for ax in ax_locations:
    ln_loc_tot, = ax.plot(dl["x_value"], dl["summ"],
                          label="Total $\u00B7 10^{-1}$", linewidth=linewidth,
                          color='k')
    ln_loc_206, = ax.plot(dl["x_value"], dl["20604"], label="Code 20604",
                          linewidth=linewidth, color='r', linestyle='--')
    ln_loc_212, = ax.plot(dl["x_value"], dl["21203"], label="Code 21203",
                          linewidth=linewidth, color='b', linestyle='--')
    ln_loc_dVIC, = ax.plot(demand_VIC_time_step, demand_VIC,
                           label="dVIC $\u00B7 2 \u00B7 10^{-2}$",
                           linewidth=linewidth, color='grey')
    ln_loc_dAdp, = ax.plot(demand_VIC_time_step, demand_VIC_adp,
                           label="dVIC + Total", linewidth=linewidth,
                           color='orange')
    ax.set_xticks(range(0, 24*8, 24))
    ax.set_xlim(0,168)
    # ax.set_ylabel("$P_{adv,\u2B26} - P_{nw,\u2B26}$ in GW", fontsize=fontsize)
    # ax_location.set_ylim(5,1.5*10**4)
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.tick_params(labelsize=fontsize)
    ax.grid(True)


offset = .05
min_top = min(min(demand_VIC), min(demand_VIC_adp))
max_top = max(max(demand_VIC), max(demand_VIC_adp))
min_bot = min(min(dl["summ"]), min(dl["20604"]), min(dl["21203"]))
max_bot = max(max(dl["summ"]), max(dl["20604"]), max(dl["21203"]))
top_ylim = [min_top - (max_top-min_top)*offset,
            max_top + (max_top-min_top)*offset]
bot_ylim = [min_bot - (max_bot-min_bot)*offset,
            max_bot + (max_bot-min_bot)*offset]

ax_locations[0].set_ylim(*top_ylim)  # outliers only
ax_locations[1].set_ylim(*bot_ylim)  # most of the data

# hide the spines between ax and ax2
ax_locations[0].spines["bottom"].set_visible(False)
ax_locations[1].spines["top"].set_visible(False)
ax_locations[1].tick_params(labeltop=False)

ax_locations[0].minorticks_on()
ax_locations[0].xaxis.set_ticks_position('none')
ax_locations[0].set_xticklabels([])

# set labels
ax_locations[1].xaxis.set_minor_locator(AutoMinorLocator())
ax_locations[1].set_xlabel(x_label, fontsize=fontsize)
ax_locations[1].text(-20, .2, "$P_{adv,\u2B26} - P_{nw,\u2B26}$ in GW",
                     va="center", ha="center", rotation="vertical",
                     fontsize=fontsize)

# set legend   
ax_locations[0].legend([ln_loc_dVIC, ln_loc_dAdp], ["dVIC", "dVIC \n + Total"], 
                       fontsize=fontsize, loc="center right",
                       bbox_to_anchor=(1.35, .5))
ax_locations[1].legend([ln_loc_tot, ln_loc_206, ln_loc_212],
                       ["Total $\u00B7 10^{-1}$", "Code 20604", "Code 21203"],
                       fontsize=fontsize, loc='center right',
                       bbox_to_anchor=(1.35, .5))
ax_locations[1].text(164, -.07, "c)", va="bottom", ha="right",
                     fontsize=fontsize)

# slants
d = .7  # proportion of vertical to horizontal extent of the slanted line
kwargs = dict(marker=[(-1, -d), (1, d)], markersize=6,
              linestyle="none", color='k', mec='k', mew=1, clip_on=False)
ax_locations[0].plot([0, 1], [0, 0], transform=ax_locations[0].transAxes, **kwargs)
ax_locations[1].plot([0, 1], [1, 1], transform=ax_locations[1].transAxes, **kwargs)

###############################################################################
###############################################################################
##                                                                           ##
##                            Difference Map Plot                            ##
##                                                                           ##
###############################################################################
###############################################################################

# plot data - geographic
# parameters to retrieve area border gps data
SA4_regions_to_include = [206,207,208,209,210,211,212,213,214]
export_SA_level = 3
_layer = "Statistical_Area_Level_" + str(export_SA_level) + "_2016"
_code = None
if 3 <= export_SA_level <= 4:
    _code = "SA" + str(export_SA_level) + "_CODE_2016"
elif export_SA_level == 2:
    _code = "SA" + str(export_SA_level) + "_MAINCODE_2016"
elif export_SA_level == 1:
    raise RuntimeError("SA code not implemented!")
else:
    raise RuntimeError("Ill defined SA code!")
# extract data from model
min_total_charge_delivered = min(location_sum.values())
max_total_charge_delivered = max(location_sum.values())
# Check if retreived data fits map data
# data retrieved from
# https://data.gov.au/data/dataset/asgs-2016-edition-boundaries
_file_name = "asgs2016absstructuresmainstructureandgccsa.gpkg"
_file_path \
    = "..\\..\\data\\generators\\locations\\sa_code, sa_names, cooridnates\\"

# choose color map
cmap = mpl.cm.bwr
# get map dimensions
parameters = Parameters()
co = ConsoleOutput()
od = OutputData(co, parameters)
map_dimensions = od.map_dimensions

# plot total charge
with fiona.open(_file_path + _file_name, layer=_layer) as layer:
    nbr_of_drawn_sas = 0
    for export_level_region in layer:
        elr = export_level_region
        is_in_selected_SA4_region = False
        for SA4_region in SA4_regions_to_include:
            if str(SA4_region) \
                == elr['properties'][_code][:len(str(SA4_region))]:
                is_in_selected_SA4_region = True
                break
        if is_in_selected_SA4_region:
            elr_code = int(elr['properties'][_code])
            charge_value = location_sum[str(elr_code)]
            color_data = get_color(cmap, charge_value,
                                   min_total_charge_delivered,
                                   max_total_charge_delivered)
            for patch_data in elr['geometry']['coordinates']:
                x = [data[0] for data in patch_data[0]]
                y = [data[1] for data in patch_data[0]]
                p = matplotlib.patches.Polygon(patch_data[0],
                                               facecolor=color_data)
                ax_map.add_patch(p)
                ax_map.plot(x, y, color='black', linewidth=linewidth_map)    
            nbr_of_drawn_sas += 1
        
            abs_limit = max(-abs(min_total_charge_delivered),
                            max_total_charge_delivered)
            
            norm = mpl.colors.Normalize(vmin=-abs_limit, vmax=abs_limit)
            divider = make_axes_locatable(ax_map)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),
                                cax=cax)
            cbar.set_label("$E_{adv,\u2B26} - E_{nw,\u2B26}$ in GWh", fontsize=fontsize)
            cbar.ax.tick_params(labelsize=fontsize)

ax_map.margins(0)
ax_map.set_xlim([map_dimensions["min_x"] ,map_dimensions["max_x"]])
ax_map.set_ylim([map_dimensions["min_y"] ,map_dimensions["max_y"]])
ax_map.axis('off')
ax_map.text(145.8, -38.5, "a)", va="bottom", ha="right", fontsize=fontsize)

###############################################################################
###############################################################################
##                                                                           ##
##                               Post-Process                                ##
##                                                                           ##
###############################################################################
###############################################################################

plt.show()

file_name = "location_time_series.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "location_time_series.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)