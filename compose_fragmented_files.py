# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 12:32:10 2022

@author: S3739258
"""

import pandas as pd
import os


mdl = 8
agents = "6k"
agents_n = 6000
pws = [(4,33)]
epcs = [(1,), (7,13), (19,25), (31,37), (43,49), (55,61), (67,73)]
s = lambda pw, epc: 1 if len(pw) + len(epc) < 4 else 2
D2_SWEEP = ["avg_cost", "avg_cost_apartment", "avg_cost_house_no_pv",
            "avg_cost_house_pv", "charge_emergency", "charge_grid",
            "charge_held_back", "charge_pv", "charge_work", "utilisation"]

# model_8_nbr_agents_6000_season_avg_avg_cost_apartment

dirs = []
files_pre = []
frmt = lambda l: f"{l[0]:0>2}" if len(l) == 1 else f"{l[0]:0>2}-{l[1]:0>2}"
frmt_d = lambda m, n, s, pw, epc: f"{n}_{s}d_mdl{m}_pw{frmt(pw)}_epc{frmt(epc)}"
frmt_f = lambda m, n: f"model_{m}_nbr_agents_{n}_season_avg_"
frmt_path = lambda d: os.path.join("results", d, "results")
frmt_path_file = lambda d, f, s: os.path.join(frmt_path(d), f"{f}{s}.csv")

# 2D Sweeps
for s2d in D2_SWEEP:
    tbl = None
    for pw in pws:
        for epc in epcs:
            d = frmt_d(mdl, agents, s(pw, epc), pw, epc)
            f = frmt_f(mdl, agents_n)
            tmp = None
            if s(pw, epc) == 2:
                tmp = pd.read_csv(frmt_path_file(d, f, s2d), index_col=0)
            else:
                tmp = pd.read_csv(frmt_path_file(d, f, "sweep_data"),
                                  index_col=0)
                tmp = tmp.loc[:, [s2d]].transpose()
                tmp.index = [epc[0]]
            tmp.columns = [f"{float(s):.02f}" for s in tmp.columns]
                
            if tbl is None:
                tbl = tmp
            else:
                tbl = tbl.append(tmp)
                
    tbl.sort_index(axis=0)
    tbl.sort_index(axis=1)
    tbl.columns = [f"{float(s):.02f}" for s in tbl.columns]
    pwf = (str(tbl.columns[0])[-2:], str(tbl.columns[-1])[-2:])
    epcf = (str(tbl.index[0])[-2:], str(tbl.index[-1])[-2:])
    df = frmt_d(mdl, agents, s(pwf, epcf), pwf, epcf)
    if not os.path.isdir(frmt_path(df)):
        os.makedirs(frmt_path(df))
    tbl.to_csv(frmt_path_file(df, frmt_f(mdl, agents), s2d))
    