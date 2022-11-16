# -*- coding: utf-8 -*-
"""
Created on Fri Jul  2 11:57:36 2021

@author: S3739258
"""

import fiona

SA4_regions_to_include = [206,207,208,209,210,211,212,213,214]
export_SA_level = 3 # e.g. for SA3 choose 3
max_distance = 0.0001 # max distance between to gps Nodes to be detected as
                      # neighbouring

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

max_distance_sqr = max_distance**2
x, y = 0, 1

export_level_region_codes = []
export_level_region_coordiantes = dict()
# data retrieved from
# https://data.gov.au/data/dataset/asgs-2016-edition-boundaries
with fiona.open('asgs2016absstructuresmainstructureandgccsa.gpkg',
                layer=_layer) as layer:
    for export_level_region in layer:
        elr = export_level_region
        is_in_selected_SA4_region = False
        for SA4_region in SA4_regions_to_include:
            if str(SA4_region) == elr['properties'][_code][:len(str(SA4_region))]:
                is_in_selected_SA4_region = True
                break
        if is_in_selected_SA4_region:
            elr_code = int(elr['properties'][_code])
            export_level_region_codes.append(elr_code)
            export_level_region_coordiantes[elr_code] = []
            for patch in elr['geometry']['coordinates']:
                c = patch[0]
                for i in range(len(patch[0])):
                    export_level_region_coordiantes[elr_code].append((c[i][x],\
                                                                      c[i][y]))

connections = []
for i in range(len(export_level_region_codes)):
    connection = []
    for j in range(len(export_level_region_codes)):
        connection.append(False)
    connections.append(connection)
    
for i_from, code_from in enumerate(export_level_region_codes):
    for i_to, code_to in enumerate(export_level_region_codes):
        if (i_to < i_from): continue
        are_neighbouring = False
        for coord_from in export_level_region_coordiantes[code_from]:
            for coord_to in export_level_region_coordiantes[code_to]:
                distance_sqr = (coord_from[0] - coord_to[0])**2 \
                               + (coord_from[1] - coord_to[1])**2
                if distance_sqr < max_distance_sqr:
                    are_neighbouring = True
                    break
            if are_neighbouring: break
        if are_neighbouring:
            connections[i_from][i_to] = True
            connections[i_to][i_from] = True
        print("From " + str(code_from) + " to " + str(code_to) + " - "\
              + str(are_neighbouring))

# Output connection matrix
header = "#"
for code in export_level_region_codes:
    header += ',' + str(code)
print(header)
for i_from in range(len(export_level_region_codes)):
    row = str(export_level_region_codes[i_from])
    for i_to in range(len(export_level_region_codes)):
        if connections[i_from][i_to]:
            row += ",1"
        else:
            row += ",0"
    print(row)

# Output connection links
print("#Start_location,End_location")
for i_from in range(len(export_level_region_codes)):
    for i_to in range(len(export_level_region_codes)):
        if i_to <= i_from: continue
        if connections[i_from][i_to] == True:
            print(str(export_level_region_codes[i_from]) + "," \
                  + str(export_level_region_codes[i_to]))