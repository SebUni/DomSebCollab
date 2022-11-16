# -*- coding: utf-8 -*-
"""
Created on Sun Jul  4 20:51:14 2021

@author: S3739258
"""

from csv_helper import CSVHelper
from cast import Cast

# select either Statistical Area 3 and 4
SA_LEVEL = 4
# do not touch
if not 1 <= SA_LEVEL <= 4:
    raise RuntimeError("Ill defined SA code!")
_filename = "SA" + str(SA_LEVEL) + "_commute_with_distances.csv"
distances = {2:[0,1,2,3], 4:[4,5,6], 6:[7,8], 8:[9,10], 10:[11,12], 12:[13,14],
             14:[15,16], 16:[17,18], 18:[19,20], 20:[21,22], 22:[23,24],
             24:[25,26], 26:[27,28], 28:[29,30], 30:[31,32], 32:[33], 34:[34],
             36:[35], 38:[36], 40:[37], 42:[38], 44:[39], 46:[40], 48:[41],
             50:[42], 52:[43], 54:[44], 56:[45], 58:[46], 60:[47], 62:[48],
             64:[49], 66:[50], 68:[51], 70:[52], 72:[53], 74:[54], 76:[55]}

nbr_of_cols = 0
distances_sorted = []
for distance, cols in distances.items():
    distances_sorted.append(distance)
    nbr_of_cols += len(cols)
distances_sorted.sort()

# read commute file
cast = Cast("Commute distances")
csv_helper = CSVHelper("",_filename)
commuters_per_sa_per_dist = dict()
area_codes = []
for row in csv_helper.data:
    area_codes.append(cast.to_positive_int(row[0], "SA area code"))
for row_it, row in enumerate(csv_helper.data):
    commuters_per_sa_per_dist[area_codes[row_it]] = dict()
    for distance, cols in distances.items():
        nbr_of_commuters = 0
        for col in cols:
            nbr_of_commuters\
                += cast.to_positive_int(row[1+col+row_it*nbr_of_cols],
                                        "Nbr of commuters")
        commuters_per_sa_per_dist[area_codes[row_it]][distance]\
            = nbr_of_commuters

rel_commuters_per_sa_per_dist = dict()
for sa, distances_in_sa in commuters_per_sa_per_dist.items():
    rel_commuters_per_sa_per_dist[sa] = dict()
    total_nbr_of_commuters = 0
    for commuters in distances_in_sa.values():
        total_nbr_of_commuters += commuters
    for distance, commuters in distances_in_sa.items():
        rel_commuters_per_sa_per_dist[sa][distance] \
            = commuters / total_nbr_of_commuters

print("#statistical_area,keys_distance_distribution," \
      + "values_distance_distribution")
for sa, distances_in_sa in rel_commuters_per_sa_per_dist.items():
    msg = ""
    msg += str(sa) + ","
    for dist_it, distance in enumerate(distances_sorted):
        msg += str(distance)
        if dist_it != len(distances_sorted) - 1:
            msg += ";"
    msg += ","
    for dist_it, distance in enumerate(distances_sorted):
        msg += str(distances_in_sa[distance])
        if dist_it != len(distances_sorted) - 1:
            msg += ";"
    print(msg)