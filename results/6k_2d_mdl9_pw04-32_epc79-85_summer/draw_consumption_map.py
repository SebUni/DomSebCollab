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

charge_values = {20601: 253.1579539585594,
 20602: 3.483884037587245,
 20603: 129.11631766631882,
 20604: 4251.435763728774,
 20605: 1093.76355358209,
 20606: 294.8871799780688,
 20607: 828.6326131264848,
 20701: 363.68545165938735,
 20702: -443.5196823683202,
 20703: 619.7829529996018,
 20801: 405.7859454328023,
 20802: -421.90293827233506,
 20803: 1052.9761630206003,
 20804: 183.48857737082548,
 20901: -525.5444903854955,
 20902: -14.674213047581588,
 20903: -1708.2405243651147,
 20904: -1540.2357053554342,
 21001: 301.8650828053717,
 21002: -219.70222320376888,
 21003: -369.9010991213378,
 21004: -386.8342187943674,
 21005: 978.32134000632,
 21101: -746.8070589547453,
 21102: -103.63362718704303,
 21103: 359.3580613371761,
 21104: -37.18195117883613,
 21105: -2255.6322354631757,
 21201: -923.6916773180974,
 21202: -407.97660799804464,
 21203: -1911.7756866957056,
 21204: 2472.887981957533,
 21205: 1003.8458990904153,
 21301: 144.2133255820586,
 21302: 131.15449706757283,
 21303: 890.1795181351729,
 21304: -1875.4093047518636,
 21305: -1336.8785907085567,
 21401: -337.36245562523936,
 21402: -2012.4249212626282}

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