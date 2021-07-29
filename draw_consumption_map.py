# -*- coding: utf-8 -*-
"""
Created on Tue Jul 27 22:49:03 2021

@author: S3739258
"""

import fiona
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches

def get_color(value, min_value, max_value):
    _max = max(abs(min_value), max_value)
    rel_value = value / _max
    if rel_value <= 0:
        return [1+rel_value,1+rel_value,1]
    else:
        return [1,1-rel_value,1-rel_value]

SA4_regions_to_include = [206,207,208,209,210,211,212,213,214]
export_SA_level = 3 # e.g. for SA3 choose 3

_layer = "Statistical_Area_Level_" + str(export_SA_level) + "_2016"
_code = None
_name = "SA" + str(export_SA_level) + "_NAME_2016"
if 3 <= export_SA_level <= 4:
    _code = "SA" + str(export_SA_level) + "_CODE_2016"
elif export_SA_level == 2:
    _code = "SA" + str(export_SA_level) + "_MAINCODE_2016"
elif export_SA_level == 1:
    raise RuntimeError("SA code not implemented!")
else:
    raise RuntimeError("Ill defined SA code!")

charge_values = {20601: -1278.3332724190818,
 20602: 35.61059313313052,
 20603: 412.45405180403054,
 20604: -6194.948711887808,
 20605: -1243.4303396031332,
 20606: -407.09826296030496,
 20607: -1396.7642235090675,
 20701: -1301.7517743688468,
 20702: 777.3441682554812,
 20703: -228.47658031329638,
 20801: -276.0715030937847,
 20802: -28.876175396208282,
 20803: -384.3102139594125,
 20804: 229.42508296770978,
 20901: -576.1337576666069,
 20902: 45.61258259702004,
 20903: 1645.8495342683655,
 20904: -648.660285630538,
 21001: -1386.2573355273526,
 21002: 1659.3732512393435,
 21003: -188.99051099444046,
 21004: 433.34099478415425,
 21005: -1582.9669524690494,
 21101: 1351.4669161596212,
 21102: 130.6676033388129,
 21103: -717.6641719844006,
 21104: 371.21048982876573,
 21105: 2273.2750825105154,
 21201: 2807.736765778929,
 21202: 1578.4545103544397,
 21203: 3313.087594979429,
 21204: -2573.047462792899,
 21205: -2713.0537689577523,
 21301: -905.9834651385527,
 21302: 356.95595767891587,
 21303: -1629.0574110093373,
 21304: 3866.808861251006,
 21305: 1775.4846799747975,
 21401: 2056.200119909127,
 21402: 1365.8827089547508}

fig = plt.figure(figsize=(13,13))
ax = fig.add_subplot(111)

# data retrieved from
# https://data.gov.au/data/dataset/asgs-2016-edition-boundaries
_file_name = "asgs2016absstructuresmainstructureandgccsa.gpkg"
_file_path = "data\\generators\\locations\\sa_code, sa_names, cooridnates\\"
export_level_region_names = dict()
with fiona.open(_file_path + _file_name, layer=_layer) as layer:
    for export_level_region in layer:
        elr = export_level_region
        is_in_selected_SA4_region = False
        for SA4_region in SA4_regions_to_include:
            if str(SA4_region) == elr['properties'][_code][:len(str(SA4_region))]:
                is_in_selected_SA4_region = True
                break
        if is_in_selected_SA4_region:
            elr_code = elr['properties'][_code]
            export_level_region_names[elr_code] = elr['properties'][_name]

if len(export_level_region_names) != len(charge_values):
    raise RuntimeError("draw_consumption.py: # of pbc values doesn't match # "\
                       + "of Stat. Areas!")

with fiona.open(_file_path + _file_name, layer=_layer) as layer:
    nbr_of_drawn_sas = 0
    for export_level_region in layer:
        elr = export_level_region
        is_in_selected_SA4_region = False
        for SA4_region in SA4_regions_to_include:
            if str(SA4_region) == elr['properties'][_code][:len(str(SA4_region))]:
                is_in_selected_SA4_region = True
                break
        if is_in_selected_SA4_region:
            elr_code = int(elr['properties'][_code])
            color_data = get_color(charge_values[elr_code],
                                   min(charge_values.values()),
                                   max(charge_values.values()))
            for patch_data in elr['geometry']['coordinates']:
                x = [data[0] for data in patch_data[0]]
                y = [data[1] for data in patch_data[0]]
                p = matplotlib.patches.Polygon(patch_data[0], facecolor=color_data)
                ax.add_patch(p)
                ax.plot(x, y, color='black', linewidth=1)    
            nbr_of_drawn_sas += 1

ax.margins(0.1)
ax.axis('off')
plt.show()
            
# print("#" + _code + "," + _name + ",latitude,longitude")
# for code in export_level_region_names.keys():
#     print(str(code) + "," + str(export_level_region_names[code]) + "," \
#           + format(export_level_region_coordiantes[code][1],".5f")+ "," \
#           + format(export_level_region_coordiantes[code][0],".5f"))