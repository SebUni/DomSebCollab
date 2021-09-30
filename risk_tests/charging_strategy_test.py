# -*- coding: utf-8 -*-
"""
Created on Wed Jul 28 15:05:58 2021

@author: S3739258
"""

from math import sqrt
import numpy as np
from scipy.special import erf, erfinv

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches
from mpl_toolkits.axes_grid1 import make_axes_locatable
cmap = mpl.cm.viridis

# SET PARAMETERS
HOME = 0
WORK = 1

activity = WORK
has_charger = True
pv_cap = 4

work_stay_duration = 8
home_stay_duration = 16

soc = 5
q_ow = 10
q_res = 5

cr_h = 2.4
cr_w = 11
cr_p = 50

p_work = 0.115
p_feed = 0.07
p_grid = 0.27
p_em = 0.5

c = 0.9

mpl.rcParams['figure.dpi'] = 300

# sweep parameters
mus = list(np.arange(0, 25, 0.1))
p_works_rough = list(np.arange(0.02, 0.33, 0.04))
p_works_fine = list(np.arange(0.02,0.33,0.001))
p_works_cents_fine = list(np.arange(2,33,0.1))

# DEFINE FUNCTIONS
def parm_cost_fct_charging_at_work_anal(q_ow, q_res, p_f, p_g, p_em, p_w, soc,
                                        c, mu, sig):
    q_tw, q_th = q_ow, q_ow + q_res
    instruction = 0
    value = q_th + q_tw - soc - mu \
        - sqrt(2) * sig * erfinv(2 * (1 - c)*(1 - (p_g - p_w)/(p_g - p_f)) - 1)
    clamped_value = min(max(value, q_th - soc), q_th + q_tw - soc)
    if p_w >= p_g:
        instruction = q_th-soc
    if p_g > p_w > p_f:
        instruction = clamped_value
    if p_f >= p_w:
        instruction = q_th + q_tw - soc
            
    return max(0, instruction)
    
def determine_charge_instructions(soc, p_work, p_feed, p_grid, p_em, q_ow,
        q_res, c, pv_cap, cr_h, cr_w, cr_p, mu, sig, activity, has_charger,
        work_stay_duration, home_stay_duration):
    charge_at_home = 0
    charge_at_work = 0
    
    if activity == WORK:
        # when agents earn more by selling PV than using it to charge
        if p_feed >= p_work:
            charge_at_work = 2 * q_ow + q_res - soc
        # when charging from grid is more expensive than at work but charging
        # from PV is better than selling PV at feed in cost
        elif p_grid >= p_work:
            # car can charge at home also from PV and forecast is not 0
            if pv_cap != 0 and has_charger and sig > 0:
                charge_at_work \
                    = parm_cost_fct_charging_at_work_anal(q_ow, q_res, p_feed,
                                        p_grid, p_em, p_work, soc, c, mu, sig)
            # car can charge at home but NOT from PV or car can NOT charge at
            # home
            else:
                charge_at_work = 2 * q_ow + q_res - soc
        # when only public charging is more expen. than work charging
        else:
            charge_at_work = q_ow + q_res - soc
        # ensure charge suffices to reach home, but uses as little public
        # charging as possible
        charge_at_work = max(charge_at_work, 0)
    if activity == HOME:
        if has_charger:
            charge_at_home = q_ow + q_res - soc
            if p_grid < p_work:
                charge_at_home += q_ow
            charge_at_home = max(charge_at_home, 0)
        else:
            charge_needed = max(q_ow + q_res - soc, 0)
            if charge_needed != 0:
                print("Emergency bla bla")
                
    return charge_at_home, charge_at_work

def add_cbar(ax, plt, norm, cmap, label):
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),
                        cax=cax)
    cbar.set_label(label)

# LOW RESOLUTION RUN - visualise dependency of optimal charging amount at work
#                      of mu
fig, ax = plt.subplots()
charge_at_work = []
for p_work in p_works_rough:
    charge_at_work.append([])
    for mu in mus:
        sig = mu / 6
        _, caw = determine_charge_instructions(soc, p_work, p_feed, p_grid,
            p_em, q_ow, q_res, c, pv_cap, cr_h, cr_w, cr_p, mu, sig, activity,
            has_charger, work_stay_duration, home_stay_duration)
        charge_at_work[-1].append(caw)
    ax.plot(mus, charge_at_work[-1], label="$p^w$ = \${:.02f}".format(p_work))
ax.set(xlabel="$\mu$ in kWh", ylabel="$q^w_0$ in kWh")
plt.legend()
plt.title("Optimal charge quantity at work")
plt.show()

min_charge = min([min(row) for row in charge_at_work])
max_charge = max([max(row) for row in charge_at_work])

fig, ax = plt.subplots()
norm = mpl.colors.Normalize(vmin=min_charge, vmax=max_charge)
ax.pcolormesh(mus, p_works_rough, charge_at_work, cmap=cmap, shading='nearest',
              vmin=min_charge, vmax=max_charge)
ax.set(xlabel="$\mu$ in kWh", ylabel="$p^w$ in \$")
add_cbar(ax, plt, norm, cmap, "$q^w_0$ in kWh")
ax.set_title("Optimal charge quantity at work")
plt.show()

# HIGH RESOLUTION
# COMPUTE DATA - ideal charge amounts and charge held back
charge_at_work = []
charge_held_back = []
for p_work in p_works_fine:
    charge_at_work.append([])
    charge_held_back.append([])
    for mu in mus:
        sig = mu / 6
        _, caw = determine_charge_instructions(soc, p_work, p_feed, p_grid,
            p_em, q_ow, q_res, c, pv_cap, cr_h, cr_w, cr_p, mu, sig, activity,
            has_charger, work_stay_duration, home_stay_duration)
        charge_at_work[-1].append(caw)
        without_forecast \
            = 2 * q_ow + q_res - soc if p_work < p_grid else q_ow + q_res - soc
        charge_held_back[-1].append((without_forecast - caw))
        
# # plot optimal charge at work
# min_charge = min([min(row) for row in charge_at_work])
# max_charge = max([max(row) for row in charge_at_work])

# fig, ax = plt.subplots()
# norm = mpl.colors.Normalize(vmin=min_charge, vmax=max_charge)
# ax.pcolormesh(mus, p_works_fine, charge_at_work, cmap=cmap, shading='gouraud',
#               vmin=min_charge, vmax=max_charge)
# ax.set(xlabel="$\mu$ in kWh", ylabel="$p^w$ in \$")
# add_cbar(ax, plt, norm, cmap, "$q^w_0$ in kWh")
# ax.set_title("Optimal charge quantity at work")
# plt.show()

# # plot how much charge is held back when considering forecasts 
# min_charge = min([min(row) for row in charge_held_back])
# max_charge = max([max(row) for row in charge_held_back])

# fig, ax = plt.subplots()
# norm = mpl.colors.Normalize(vmin=min_charge, vmax=max_charge)
# ax.pcolormesh(mus, p_works_fine, charge_held_back, cmap=cmap,shading='gouraud',
#               vmin=min_charge, vmax=max_charge)
# ax.set(xlabel="$\mu$ in kWh", ylabel="$p^w$ in \$")
# add_cbar(ax, plt, norm, cmap, "$q^{hb}_0$ in kWh")
# ax.set_title("Charge held back at work")
# plt.show()

fontsize=8
cm = 1/2.54

cmap = mpl.cm.viridis
x_label = "$\mu$ in kWh"
y_label = "$p^w$ in $10^{-2}$ \$/kWh"
z_label_left = "$q^w$ in kWh"
z_label_right = "$q^{hb}$ in kWh"

fig = plt.figure(figsize=(16*cm, 5*cm))
gs = fig.add_gridspec(1, 2, wspace=1.4*cm)
ax = gs.subplots(sharex=False, sharey=False)

vmin_left=min([min(row) for row in charge_at_work])
vmin_right=min([min(row) for row in charge_held_back])
vmax_left=max([max(row) for row in charge_at_work])
vmax_right=max([max(row) for row in charge_held_back])
norm_left = mpl.colors.Normalize(vmin=vmin_left, vmax=vmax_left)
norm_right = mpl.colors.Normalize(vmin=vmin_left, vmax=vmax_right)

ax[0].pcolormesh(mus, p_works_cents_fine, charge_at_work, cmap=cmap,
              shading='gouraud', vmin=vmin_left, vmax=vmax_left)
ax[0].set_xlabel(x_label, fontsize=fontsize)
ax[0].set_ylabel(y_label, fontsize=fontsize)
ax[0].minorticks_on()
ax[0].tick_params(labelsize=fontsize)

divider = make_axes_locatable(ax[0])
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm_left,cmap=cmap),
                    cax=cax)
cbar.minorticks_on()
cbar.ax.tick_params(labelsize=fontsize)
cbar.set_label(z_label_left, fontsize=fontsize)
ax[0].text(24, 32, "a)", va="top", ha="right", fontsize=fontsize, color='w')

ax[1].pcolormesh(mus, p_works_cents_fine, charge_held_back, cmap=cmap,
              shading='gouraud', vmin=vmin_right, vmax=vmax_right)
ax[1].set_xlabel(x_label, fontsize=fontsize)
ax[1].set_ylabel(y_label, fontsize=fontsize)
ax[1].minorticks_on()
ax[1].tick_params(labelsize=fontsize)
ax[1].text(24, 32, "b)", va="top", ha="right", fontsize=fontsize, color='w')

divider = make_axes_locatable(ax[1])
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm_right,cmap=cmap),
                    cax=cax)
cbar.minorticks_on()
cbar.ax.tick_params(labelsize=fontsize)
cbar.set_label(z_label_right, fontsize=fontsize)

plt.show()

file_name = "cost_fct_anal.pdf"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)
file_name = "cost_fct_anal.png"
fig.savefig(file_name, bbox_inches='tight', pad_inches=0.01)

