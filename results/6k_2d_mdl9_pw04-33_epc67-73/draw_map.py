# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 09:26:58 2021

@author: S3739258
"""
import fiona

import matplotlib.pyplot as plt
import matplotlib.patches
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable


from parameters import Parameters
from output_data import OutputData
from console_output import ConsoleOutput
from cast import Cast
from csv_helper import CSVHelper

MY_DPI = 96

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
# Check if retreived data fits map data
# data retrieved from
# https://data.gov.au/data/dataset/asgs-2016-edition-boundaries
_file_name = "asgs2016absstructuresmainstructureandgccsa.gpkg"
_file_path \
    = "data\\generators\\locations\\sa_code, sa_names, cooridnates\\"

# get map dimensions
parameters = Parameters()
co = ConsoleOutput()
od = OutputData(co, parameters)
map_dimensions = od.map_dimensions

# get area centers
cast = Cast("Location")
locations = {}
csv_helper = CSVHelper("data/SA" + str(export_SA_level),"locations.csv")
for row in csv_helper.data:
    uid = cast.to_positive_int(row[0], "Uid")
    locations[uid] = (cast.to_float(row[2], "Longitude"),
                      cast.to_float(row[3], "Latitude"))
    
# load road data
cast = Cast("Connection")
roads = {}
csv_helper = CSVHelper("data/SA" + str(export_SA_level),"connections.csv")
for row in csv_helper.data:
    start_location_uid = cast.to_int(row[0], "start_location_uid")
    end_location_uid = cast.to_int(row[1], "end_location_uid")
    roads[start_location_uid] = end_location_uid

# plot total charge
fig = plt.figure(figsize=(1080 / MY_DPI, 1080 / MY_DPI))
ax = fig.add_subplot(111)
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
            color_data =[1, 1, 1]
            for patch_data in elr['geometry']['coordinates']:
                x = [data[0] for data in patch_data[0]]
                y = [data[1] for data in patch_data[0]]
                p = matplotlib.patches.Polygon(patch_data[0],
                                               facecolor=color_data)
                ax.add_patch(p)
                ax.plot(x, y, color='lightgrey', linewidth=1, zorder=1)    
            nbr_of_drawn_sas += 1

ax.margins(0.1)
ax.set_xlim([map_dimensions["min_x"] ,map_dimensions["max_x"]])
ax.set_ylim([map_dimensions["min_y"] ,map_dimensions["max_y"]])
ax.axis('off')
plt.show()
fig.savefig("mappy_the_map_with_patchies_only.svg", bbox_inches='tight', pad_inches=0.1, dpi=MY_DPI)

fig = plt.figure(figsize=(1080 / MY_DPI, 1080 / MY_DPI))
ax = fig.add_subplot(111)

# get & plot area centers
cast = Cast("Location")
locations = {}
csv_helper = CSVHelper("data/SA" + str(export_SA_level),"locations.csv")
for row in csv_helper.data:
    uid = cast.to_positive_int(row[0], "Uid")
    locations[uid] = (cast.to_float(row[2], "Longitude"),
                      cast.to_float(row[3], "Latitude"))
    gps = locations[uid]
    ax.scatter(gps[0], gps[1], s=100, color='black', zorder=2)

# get & plot roads
cast = Cast("Connection")
csv_helper = CSVHelper("data/SA" + str(export_SA_level),"connections.csv")
for row in csv_helper.data:
    start_location_uid = cast.to_int(row[0], "start_location_uid")
    end_location_uid = cast.to_int(row[1], "end_location_uid")
    start_gps = locations[start_location_uid]
    end_gps = locations[end_location_uid]
    ax.plot([start_gps[0], end_gps[0]], [start_gps[1], end_gps[1]],
            color='black', zorder=3)
    
ax.margins(0.1)
ax.set_xlim([map_dimensions["min_x"] ,map_dimensions["max_x"]])
ax.set_ylim([map_dimensions["min_y"] ,map_dimensions["max_y"]])
ax.axis('off')
plt.show()
fig.savefig("mappy_the_map_with_griddy_grizzly_only.svg", bbox_inches='tight', pad_inches=0.1, dpi=MY_DPI)