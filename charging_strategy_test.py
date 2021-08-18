# -*- coding: utf-8 -*-
"""
Created on Wed Jul 28 15:05:58 2021

@author: S3739258
"""

import math
from math import sqrt
import numpy as np
from scipy.special import erf, erfinv

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches
from mpl_toolkits.axes_grid1 import make_axes_locatable

def parm_cost_fct_charging_at_work_anal(q_ow, q_res, p_f, p_g, p_em, p_w, soc,
                                        c, mu, sig):
    q_tw, q_th = q_ow, q_ow + q_res
    sqrt2sig = math.sqrt(2) * sig
    # performance helper
    thresh = mu + sqrt2sig * erfinv(1 - 2*c)
    # shorthands
    dp = p_g - p_f
    dp_div = dp / (2 * (1 - c))
    
    instruction = 0
    instruction_command = -1
    
    value = q_th + q_tw - soc - mu - sqrt(2) * sig * erfinv(2*(1-c)*(1-(p_g-p_w)/(p_g-p_f))-1)
    clamped_value = min(max(value,
                   q_th - soc),
               q_th + q_tw - soc)
    if p_w >= p_g:
        instruction = q_th-soc
    if p_g > p_w > p_f:
        instruction = clamped_value
    if p_f >= p_w:
        instruction = q_th + q_tw - soc
            
    return max(0, instruction), instruction_command
    
def determine_charge_instructions(soc, p_work, p_feed, p_grid, p_em, q_ow,
        q_res, c, pv_cap, cr_h, cr_w, cr_p, mu, sig, activity, has_charger,
        work_stay_duration, home_stay_duration):
    charge_at_home = 0
    charge_at_work = 0
    instruction_command = -1
    
    if activity == WORK:
        # when agents earn more by selling PV than using it to charge
        if p_feed >= p_work:
            charge_at_work = 2 * q_ow + q_res - soc
            instruction_command = 10
        # when charging from grid is more expensive than at work but charging
        # from PV is better than selling PV at feed in cost
        elif p_grid >= p_work:
            # car can charge at home also from PV and forecast is not 0
            if pv_cap != 0 and has_charger and sig > 0:
                charge_at_work, instruction_command \
                    = parm_cost_fct_charging_at_work_anal(q_ow, q_res, p_feed,
                                        p_grid, p_em, p_work, soc, c, mu, sig)
            # car can charge at home but NOT from PV or car can NOT charge at
            # home
            else:
                charge_at_work = 2 * q_ow + q_res - soc
                instruction_command =  11
        # when only public charging is more expen. than work charging
        else:
            charge_at_work = q_ow + q_res - soc
            instruction_command = 12
        # ensure charge suffices to reach home, but uses as little public
        # charging as possible
        charge_at_work = max(charge_at_work, 0)
    if activity == HOME:
        if has_charger:
            charge_at_home = q_ow + q_res - soc
            instruction_command = 13
            if p_grid < p_work:
                charge_at_home += q_ow
                instruction_command = 14
            charge_at_home = max(charge_at_home, 0)
        else:
            charge_needed = max(q_ow + q_res - soc, 0)
            instruction_command = 15
            if charge_needed != 0:
                print("Emergency bla bla")
                
    return charge_at_home, charge_at_work, instruction_command

HOME = 0
WORK = 1

activity = WORK
has_charger = True
pv_cap = 4

work_stay_duration = 8
home_stay_duration = 16

soc = 20
q_ow = 20
q_res = 5

cr_h = 2.4
cr_w = 11
cr_p = 50

p_work = 0.16
p_feed = 0.11
p_grid = 0.21
p_em = 0.5

c = 0.7
mu = 10
sig = 20

# 1 dim
mus = list(np.arange(0, 50, 0.01))

charge_at_work = []
instruction_commands = []
for mu in mus:
    _, caw, ic = determine_charge_instructions(soc, p_work, p_feed, p_grid,
        p_em, q_ow, q_res, c, pv_cap, cr_h, cr_w, cr_p, mu, sig, activity,
        has_charger, work_stay_duration, home_stay_duration)
    charge_at_work.append(caw)
    instruction_commands.append(ic)

fig, ax = plt.subplots()
ax.plot(mus, charge_at_work)
ax.set(xlabel="mu", ylabel="charge_at_work")
plt.title("charge_at_work")
plt.show()

# 2 dim
p_works = list(np.arange(0.08,0.25,0.0075))
mus = list(np.arange(0, 50, 0.1))

charge_at_work = []
for p_work in p_works:
    charge_at_work.append([])
    for mu in mus:
        _, caw, ic = determine_charge_instructions(soc, p_work, p_feed,
            p_grid, p_em, q_ow, q_res, c, pv_cap, cr_h, cr_w, cr_p, mu, sig,
            activity, has_charger, work_stay_duration, home_stay_duration)
        charge_at_work[-1].append(caw)
min_charge = min([min(row) for row in charge_at_work])
max_charge = max([max(row) for row in charge_at_work])

cmap = mpl.cm.viridis
fig, ax = plt.subplots()
norm = mpl.colors.Normalize(vmin=min_charge, vmax=max_charge)
ax.pcolormesh(mus, p_works, charge_at_work, cmap=cmap, shading='gouraud',
              vmin=min_charge, vmax=max_charge)
ax.set(xlabel="mus", ylabel="p_works")

divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),
                    cax=cax)
cbar.set_label("charge_at_work")

ax.set_title("charge_at_work")
plt.show()