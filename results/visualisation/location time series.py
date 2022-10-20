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
maw = 6

# charge recieved by source
file_source = "model_1-6_nbr_agents_12000_season_avg-avg_-_diff_charge_received_time_series.csv"
# charge received by location
file_location = "model_1-6_nbr_agents_12000_season_avg-avg_-_diff_location_time_series.csv"

names = ["source","location"]
files = [file_source, file_location]

            
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
        
# moving average
maw = 6
data_maw6 = dict()
for name, data_set in data_raw.items():
    data_maw6[name] = dict()
    for col_name, col_data in data_set.items():
        if col_name == "x_value":
            data_maw6[name][col_name] = col_data
        else:
            data_maw6[name][col_name] = []
            for it, value in enumerate(col_data):
                start_it = it - maw // 2
                end_it = start_it + maw
                _sum = 0
                for i in range(0, maw):
                    _sum += col_data[(start_it + i) % len(col_data)]
                avg_value = _sum / maw
                data_maw6[name][col_name].append(avg_value)
  
maw = 12
data_maw12 = dict()
for name, data_set in data_raw.items():
    data_maw12[name] = dict()
    for col_name, col_data in data_set.items():
        if col_name == "x_value":
            data_maw12[name][col_name] = col_data
        else:
            data_maw12[name][col_name] = []
            for it, value in enumerate(col_data):
                start_it = it - maw // 2
                end_it = start_it + maw
                _sum = 0
                for i in range(0, maw):
                    _sum += col_data[(start_it + i) % len(col_data)]
                avg_value = _sum / maw
                data_maw12[name][col_name].append(avg_value)

demand_VIC = []
demand_VIC_time_step = np.arange(0,168,.5)
cast = Cast("demand VIC")
csv_helper = CSVHelper("results", "demand_VIC.csv", skip_header=True)
for row in csv_helper.data:
    demand_VIC.append(cast.to_float(row[2],"demand"))
# min_value = min(demand_VIC)
# demand_VIC = [value - min_value for value in demand_VIC]
max_value = max(demand_VIC)
max_total = max(data_maw12["location"]["summ"])
print(max_total / max_value)
demand_VIC = [value * max_total / max_value for value in demand_VIC]

cast = Cast("Analysis")

x_label = "$t$ in h"

linewidth = .8
linewidth_map = 0.3
cm = 1/2.54
fontsize=8

fig = plt.figure(figsize=(7.5, 16*cm))

ax_source = fig.add_axes([0.125, 0.58, 0.38, 0.3])
ax_map = fig.add_axes([0.54, 0.54, 0.302, 0.34])
ax_location = fig.add_axes([0.125, 0.356, 0.60, 0.15])
# ax_location = fig.add_axes([0.125, 0.356, 0.775, 0.15])
"""
ax_location_zoom_left = fig.add_axes([0.125, 0.125, 0.385, 0.15])
ax_location_zoom_right = fig.add_axes([0.515, 0.125, 0.385, 0.15])
"""

# ax_source = plt.subplot(221)
# ax_map = plt.subplot(222)
# ax_location = plt.subplot(413)
# ax_location_zoom_left = plt.subplot(427)
# ax_location_zoom_right = plt.subplot(428)

ax_source.plot(data_maw12["source"]["x_value"], data_maw12["source"]["charge_received_grid"], label="Grid", linewidth=linewidth, color='k')
ax_source.plot(data_maw12["source"]["x_value"], data_maw12["source"]["charge_received_pv"], label="PV", linewidth=linewidth, color='g')
ax_source.plot(data_maw12["source"]["x_value"], data_maw12["source"]["charge_received_work"], label="Work", linewidth=linewidth, color='r')
ax_source.plot(data_maw12["source"]["x_value"], data_maw12["source"]["charge_received_public"], label="Public", linewidth=linewidth, color='b')
ax_source.set_xlabel(x_label, fontsize=fontsize)
ax_source.xaxis.set_minor_locator(AutoMinorLocator())
ax_source.set_xticks(range(0, 24*8, 24))
ax_source.set_xlim(0,168)
ax_source.set_ylabel("$P_{adv,\u26AA} - P_{nw,\u26AA}$ in GW", fontsize=fontsize)
# ax_source.set_ylim(5,1.5*10**4)
ax_source.yaxis.set_minor_locator(AutoMinorLocator())
ax_source.tick_params(labelsize=fontsize)
ax_source.grid(True)
ax_source.legend(fontsize=fontsize,loc=1)
ax_source.text(160, -0.9, "a)", va="bottom", ha="right", fontsize=fontsize)

ax_location.plot(data_maw12["location"]["x_value"], data_maw12["location"]["summ"], label="Total $\u00B7 10^{-1}$", linewidth=linewidth, color='k')
ax_location.plot(data_maw12["location"]["x_value"], data_maw12["location"]["20604"], label="Code 20604", linewidth=linewidth, color='r')
ax_location.plot(data_maw12["location"]["x_value"], data_maw12["location"]["21203"], label="Code 21203", linewidth=linewidth, color='b')
ax_location.plot(demand_VIC_time_step, demand_VIC, label="dVIC $\u00B7 2 \u00B7 10^{-2}$", linewidth=linewidth, color='grey', linestyle='--')
ax_location.set_xlabel(x_label, fontsize=fontsize)
ax_location.xaxis.set_minor_locator(AutoMinorLocator())
ax_location.set_xticks(range(0, 24*8, 24))
ax_location.set_xlim(0,168)
ax_location.set_ylabel("$P_{adv,\u2B26} - P_{nw,\u2B26}$ in GW", fontsize=fontsize)
# ax_location.set_ylim(5,1.5*10**4)
ax_location.yaxis.set_minor_locator(AutoMinorLocator())
ax_location.tick_params(labelsize=fontsize)
ax_location.grid(True)
ax_location.legend(fontsize=fontsize, loc='center right',
                              bbox_to_anchor=(1.3, 0.5))
ax_location.text(164, -.07, "c)", va="bottom", ha="right", fontsize=fontsize)

"""
ax_location_zoom_left.plot(data_maw6["location"]["x_value"], data_maw6["location"]["summ"], label="Total", linewidth=linewidth, color='k')
ax_location_zoom_left.plot(data_maw6["location"]["x_value"], data_maw6["location"]["20604"], label="20604", linewidth=linewidth, color='r')
ax_location_zoom_left.plot(data_maw6["location"]["x_value"], data_maw6["location"]["21203"], label="21203", linewidth=linewidth, color='b')
ax_location_zoom_left.plot(demand_VIC_time_step, demand_VIC, label="demand VIC", linewidth=linewidth, color='grey', linestyle='--')
ax_location_zoom_left.set_xlabel(x_label, fontsize=fontsize)
ax_location_zoom_left.xaxis.set_minor_locator(AutoMinorLocator())
ax_location_zoom_left.set_xticks(range(0, 24*8, 24))
ax_location_zoom_left.set_xlim(0,25)
ax_location_zoom_left.set_ylabel("$cr^{ts}_{adv,\u2B26} - cr^{ts}_{nw,\u2B26}$ in GW", fontsize=fontsize)
# ax_location_zoom_left.set_ylim(5,1.5*10**4)
ax_location_zoom_left.yaxis.set_minor_locator(AutoMinorLocator())
ax_location_zoom_left.tick_params(labelsize=fontsize)
ax_location_zoom_left.grid(True)

ax_location_zoom_right.plot(data_maw6["location"]["x_value"], data_maw6["location"]["summ"], label="Total $*10^{-1}$", linewidth=linewidth, color='k')
ax_location_zoom_right.plot(data_maw6["location"]["x_value"], data_maw6["location"]["20604"], label="Code 20604", linewidth=linewidth, color='r')
ax_location_zoom_right.plot(data_maw6["location"]["x_value"], data_maw6["location"]["21203"], label="Code 21203", linewidth=linewidth, color='b')
ax_location_zoom_right.plot(demand_VIC_time_step, demand_VIC, label="dVIC * 0.02", linewidth=linewidth, color='grey', linestyle='--')
ax_location_zoom_right.set_xlabel(x_label, fontsize=fontsize)
ax_location_zoom_right.xaxis.set_minor_locator(AutoMinorLocator())
ax_location_zoom_right.set_xlim(143,168)
ax_location_zoom_right.set_xticks([144,168])
# ax_location_zoom_right.set_yticks()
ax_location_zoom_right.set_yticklabels([])
ax_location_zoom_right.yaxis.tick_right()
# ax_location_zoom_right.set_ylim(5,1.5*10**4)
ax_location_zoom_right.tick_params(labelsize=fontsize)
ax_location_zoom_right.grid(True)
ax_location_zoom_right.legend(fontsize=fontsize, loc='upper left',
                              bbox_to_anchor=(-.16, 1.02))

ax_location_zoom_left.spines['right'].set_visible(False)
ax_location_zoom_right.spines['left'].set_visible(False)
d = 3  # proportion of vertical to horizontal extent of the slanted line
kwargs = dict(marker=[(-1, -d), (1, d)], markersize=12,
              linestyle="none", color='k', mec='k', mew=1, clip_on=False)
ax_location_zoom_left.plot([1, 1], [1, 0], transform=ax_location_zoom_left.transAxes, **kwargs)
ax_location_zoom_right.plot([0, 0], [1, 0], transform=ax_location_zoom_right.transAxes, **kwargs)
ax_location_zoom_right.text(167, -.08, "d)", va="bottom", ha="right", fontsize=fontsize)
"""

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
ax_map.text(145.8, -38.5, "b)", va="bottom", ha="right", fontsize=fontsize)

plt.show()

file_name = "location_time_series.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "location_time_series.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)