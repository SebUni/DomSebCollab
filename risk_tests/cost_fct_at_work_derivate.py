# -*- coding: utf-8 -*-
"""
Created on Wed Aug 18 09:43:56 2021

@author: S3739258
"""

from numpy import sqrt, exp, pi, arange
from scipy.special import erf, erfinv
import matplotlib.pyplot as plt

# SET PARAMETERS
q_ow = 10
soc = 5

q_w = list(arange(q_ow - soc, 2* q_ow - soc + .1, .1))
c = 0.9
mu = arange(5,35,5)
sig = 5
p_p = 0.5
p_g = 0.25
p_w = 0.35
p_f = 0.1

# DEFINE FUNCTIONS
def psi(q_h, mu, sig, c):
    return q_h-mu-max(q_h-mu-sqrt(2)*sig*erfinv(1-2*c),0)

def N(x, mu, sig):
    ''' Normal distribution evaluated at x. '''
    return (1 / (sqrt(2 * pi) * sig)) * exp(- (x - mu)**2 / (2 * sig**2))

def CVaR(q_w, q_ow, soc, mu, sig, c, p_f, p_g):
    q_h = max(0, 2 * q_ow - soc - q_w)
    dp = p_g - p_f
    _psi = psi(q_h, mu, sig, c)
    return dp * (q_h - _psi - mu \
                 + (1/(1-c)) * ((_psi/2)*(erf(_psi/(sqrt(2)*sig))+1)\
                                + sig**2 * N(_psi, 0, sig)))
        
def C(q_w, q_ow, soc, mu, sig, c, p_f, p_g):
    q_h = max(2*q_ow-soc-q_w,0)
    return q_w*p_w + q_h*p_f \
        + (max(q_ow - soc - q_w, 0)+max(q_ow-max(soc+q_w-q_ow, 0)-q_h, 0))*p_p\
        + CVaR(q_w, q_ow, soc, mu, sig, c, p_f, p_g)
        
def C_deri(q_w, q_ow, soc, mu, sig, c, p_f, p_g):
    dp = p_g - p_f
    return p_w - p_g \
        - dp * ((1 / (2 * (1 - c)))\
                * (erf((2 * q_ow - soc - q_w - mu) / (sqrt(2) * sig)) + 1) -1)\
                    * (q_w >= 2 * q_ow - soc - mu - sqrt(2) *sig*erfinv(1-2*c))
            
def C_deri_root(q_ow, soc, mu, sig, c, p_f, p_g):
    value = 2 * q_ow - soc - mu \
        - sqrt(2) * sig * erfinv(2 * (1 - c) * (1 - (p_g-p_w)/(p_g-p_f)) - 1)
    return min(max(value, q_ow - soc), 2 * q_ow - soc)

# RUN FUNCTIONS
# show cost function
for mu_slct in mu:
    y = [C(q_w_slct, q_ow, soc, mu_slct, sig, c, p_f, p_g) for q_w_slct in q_w]
    plt.plot(q_w, y, label="mu = {:.01f}".format(mu_slct))
plt.title("Cost function C(q_h(q_w))")
plt.xlabel("q^w in kWh")
plt.ylabel("C(q_h(q_w))")
plt.legend()
plt.show()
# show cost function derivative
for mu_slct in mu:
    y = [C_deri(q_w_slct, q_ow, soc, mu_slct, sig, c, p_f, p_g)\
         for q_w_slct in q_w]
    plt.plot(q_w, y, label="mu = {:.01f}".format(mu_slct))
plt.title("Cost function derivative d/dq_w C(q_h(q_w))")
plt.xlabel("q^w in kWh")
plt.ylabel("d/dq_w C(q_h(q_w)) in $/kWh")
plt.legend()
plt.show()
# print roots of derivative
for mu_slct in mu:
    para = "q_ow = {:.01f} kWh, soc = {:.01f} kWh, c = {:.02f}, " \
        + "mu_slct = {:d} kWh, sig = {:d} kWh"
    print(para.format(q_ow, soc, c, mu_slct, sig))
    para = "p_p = ${:.03f}, p_g = ${:.03f}, p_w = ${:.03f}, p_f = ${:.03f}"
    print(para.format(p_p, p_g, p_w, p_f))
    if p_w > p_g:
        print("Root: {:.02f} kWh".format(q_ow-soc))
    if p_w == p_g:
        print("Root in [{:.02f} kWh, {:.02f} kWh]".format(q_ow-soc,
                            C_deri_root(q_ow, soc, mu_slct, sig, c, p_f, p_g)))
    if p_g > p_w > p_f:
        print("Root: {:.02f} kWh".format(C_deri_root(q_ow, soc, mu_slct, sig,
                                                     c, p_f, p_g)))
    if p_f >= p_w:
        print("Root: {:.02f} kWh".format(2*q_ow-soc))
    print("")
        