# -*- coding: utf-8 -*-
"""
Created on Fri Jul  2 11:57:36 2021

@author: S3739258
"""

import fiona

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
    
x, y = 0, 1

export_level_region_names = dict()
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
            elr_code = elr['properties'][_code]
            # calc surface and centroid https://wiki2.org/en/Centroid+Brights.4
            surface_areas = []
            centroids_x = []
            centroids_y = []
            for patch in elr['geometry']['coordinates']:
                c = patch[0]
                surface_area = 0
                Cx, Cy = 0, 0
                for i in range(len(patch[0])-1):
                    z = c[i][x] * c[i+1][y] - c[i+1][x] * c[i][y]
                    surface_area += z
                    Cx += (c[i][x] + c[i+1][x]) * z
                    Cy += (c[i][y] + c[i+1][y]) * z
                surface_area /= 2
                C = (Cx / (6 * surface_area), Cy / (6 * surface_area))
                surface_areas.append(surface_area)
                centroids_x.append(Cx / (6 * surface_area))
                centroids_y.append(Cy / (6 * surface_area))
                
            centroid_x, centroid_y = 0, 0
            for i in range(len(surface_areas)):
                centroid_x += centroids_x[i]*surface_areas[i]
                centroid_y += centroids_y[i]*surface_areas[i]
            centroid_x /= sum(surface_areas)
            centroid_y /= sum(surface_areas)
            
            export_level_region_names[elr_code] = elr['properties'][_name]
            export_level_region_coordiantes[elr_code] \
                = (centroid_x, centroid_y)
            
print("#" + _code + "," + _name + ",latitude,longitude")
for code in export_level_region_names.keys():
    print(str(code) + "," + str(export_level_region_names[code]) + "," \
          + format(export_level_region_coordiantes[code][1],".5f")+ "," \
          + format(export_level_region_coordiantes[code][0],".5f"))