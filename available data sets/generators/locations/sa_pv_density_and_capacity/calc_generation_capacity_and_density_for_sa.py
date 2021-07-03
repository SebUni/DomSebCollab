# -*- coding: utf-8 -*-
"""
Created on Sat Jul  3 20:17:52 2021

@author: S3739258
"""

import csv
from csv_helper import CSVHelper
from cast import Cast

SA4_regions_to_include = [206,207,208,209,210,211,212,213,214]
# select either Statistical Area 3 and 4
export_SA_level = 4
# do not touch
_sa_column = None
if export_SA_level == 4:
    _sa_column = 3
elif export_SA_level == 3:
    _sa_column = 1
elif 1 <= export_SA_level <= 2:
    raise RuntimeError("SA code not implemented!")
else:
    raise RuntimeError("Ill defined SA code!")

# pv assets for statistical area
cast = Cast("Mesh Block to Post Area")
csv_helper = CSVHelper("","mesh_block_to_postal_area.csv")
mesh_block_to_postal_area = dict()
for row in csv_helper.data:
    mesh_block = cast.to_positive_int(row[0], "mesh_block")
    postal_area = cast.to_positive_int(row[1], "postal_area")
    mesh_block_to_postal_area[mesh_block] = postal_area

cast = Cast("Mesh Block to Statistical Area")
csv_helper = CSVHelper("","mesh_block_to_statistical_area.csv")
mesh_block_to_sa = dict()
for row in csv_helper.data:
    mesh_block = cast.to_positive_int(row[0], "mesh_block")
    sa4_lvl = cast.to_positive_int(row[3], "sa4 level")
    if sa4_lvl not in SA4_regions_to_include: continue
    sa_slctd_lvl = cast.to_positive_int(row[_sa_column], "statictical_area")
    mesh_block_to_sa[mesh_block] = sa_slctd_lvl

cast = Cast("PV Count and Capacity in Postal Area")
csv_helper = CSVHelper("","pv_density_and_capacity.csv")
pv_capacity_in_postcode_area = dict()
pv_count_in_postcode_area = dict()
estimated_suitable_dwellings_in_postcode_area = dict()
for row in csv_helper.data:
    postcode_area = cast.to_positive_int(row[0], "postcode_area")
    # over 10 kW is assumed to be commercial as suggested in
    # https://pv-map.apvi.org.au/historical#12/-37.8160/144.9639
    pv_capacity_in_postcode_area[postcode_area] \
        = cast.to_positive_float(row[5], "pv capacity under 10 kW")
    pv_count_in_postcode_area[postcode_area] \
        = cast.to_positive_int(row[8], "pv count under 10 kW")
    estimated_suitable_dwellings_in_postcode_area[postcode_area] \
          = cast.to_positive_int(row[2], "estimated suitable dwellings")

# assign postal areas to statistical areas
mesh_blocks_in_sa = dict()
for mesh_block in mesh_block_to_sa.keys():
    sa = mesh_block_to_sa[mesh_block]
    if sa not in mesh_blocks_in_sa.keys():
        mesh_blocks_in_sa[sa] = []
    mesh_blocks_in_sa[sa].append(mesh_block)
    
mesh_blocks_in_postal_area = dict()
for mesh_block in mesh_block_to_postal_area.keys():
    postal_area = mesh_block_to_postal_area[mesh_block]
    if postal_area not in mesh_blocks_in_postal_area.keys():
        mesh_blocks_in_postal_area[postal_area] = []
    mesh_blocks_in_postal_area[postal_area].append(mesh_block)
    
postal_areas_in_sas = dict()
for postal_area, mesh_blocks in mesh_blocks_in_postal_area.items():
    # check which statisitcal areas the mesh blocks of a postal area lie in
    occurence_in_sa = dict()
    for mesh_block in mesh_blocks:
        if mesh_block not in mesh_block_to_sa.keys():
            continue
        sa = mesh_block_to_sa[mesh_block]
        if sa not in occurence_in_sa.keys():
            occurence_in_sa[sa] = 0
        occurence_in_sa[sa] += 1
    # check which statistical area most mesh block lie in
    highest_mesh_block_count = 0
    most_suitable_sa = -1
    for sa, count in occurence_in_sa.items():
        if count > highest_mesh_block_count:
            most_suitable_sa = sa
            highest_mesh_block_count = count
    if most_suitable_sa == -1: continue
    if most_suitable_sa not in postal_areas_in_sas.keys():
        postal_areas_in_sas[most_suitable_sa] = []
    postal_areas_in_sas[most_suitable_sa].append(postal_area)

# assign pv capacity and density to statistical areas
avg_pv_capacity_in_sa = dict()
pv_density_in_sa = dict()
for sa, postal_areas in postal_areas_in_sas.items():
    pv_capacity = 0
    pv_count = 0
    nbr_suitable_dwellings = 0
    for postal_area in postal_areas:
        if postal_area not in pv_capacity_in_postcode_area: continue
        pv_capacity += pv_capacity_in_postcode_area[postal_area]
        pv_count += pv_count_in_postcode_area[postal_area]
        nbr_suitable_dwellings \
            += estimated_suitable_dwellings_in_postcode_area[postal_area]
        test = 0
    pv_density_in_sa[sa] = pv_count / nbr_suitable_dwellings
    avg_pv_capacity_in_sa[sa] = pv_capacity / pv_count

# save to csv
header = "#StatisticalArea,PV_denisty,Avg_pv_capacity"
file_name = "output_SA" + str(export_SA_level) + "_pv_density_and_capacity.csv"
with open(file_name, mode='w') as pv_density_and_capacity_file:
    wr = csv.writer(pv_density_and_capacity_file, delimiter=',', quotechar='"',
                    quoting=csv.QUOTE_MINIMAL)
    wr.writerow(header.split(","))
    for sa, density in pv_density_in_sa.items():
        row = str(sa) + "," + str(density) + "," \
            + str(avg_pv_capacity_in_sa[sa])
        wr.writerow([row])
