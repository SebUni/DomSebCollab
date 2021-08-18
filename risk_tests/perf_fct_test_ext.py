# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 21:30:24 2021

@author: S3739258
"""

from numpy import inf, sqrt, exp, pi, arange
from scipy.special import erf, erfinv
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
import matplotlib.pyplot as plt

def root_analytic(q_h, c, mu, sig, p_g, p_f):
    dp = p_g + p_f
    return max(dp * (q_h - mu - sqrt(2) * sig * erfinv(1 - 2 * c)), 0.0)

def perf_fct_ana(phi, q_h, c, mu, sig, p_g, p_f):
    integral = 0;
    dp = p_g + p_f
    if phi >= 0:
        integral = ((- phi / dp - (mu - q_h)) / 2) \
            * (erf((- phi / dp - (mu - q_h)) / (sqrt(2) * sig)) + 1)\
            + sig**2 * N(- phi / dp, mu - q_h, sig)
    else:
        integral = ((q_h - mu) / 2) \
            * (erf((q_h - mu) / (sqrt(2) * sig)) + 1)\
            + sig**2 * N(0, mu - q_h, sig) - phi / dp
    return phi + (dp / (1 - c)) * integral

def slvd_perf_fct(q_h, c, mu, sig, p_g, p_f):
    dp = p_g + p_f
    phi_0 = root_analytic(q_h, c, mu, sig, p_g, p_f)
    psi = q_h - mu - phi_0 / dp
    return dp * (q_h - psi - mu + (1 / (1 - c)) \
        * ((psi / 2) * (erf(psi/(sqrt(2) * sig))+1) + sig**2 * N(psi, 0, sig)))

def perf_fct_prt(phi, q_h, c, mu, sig, p_g, p_f):
    integral = 0;
    dp = p_g + p_f
    
    integrant_1 = lambda q_R : (dp*(q_h-q_R)-phi)*N(q_R,mu,sig)
    integrant_2 = lambda q_R : - phi * N(q_R,mu,sig)
        
    if phi >= 0:
        integral, _ = quad(integrant_1, - inf, q_h - phi / dp)
    else:
        integral_1, _ = quad(integrant_1, -inf, q_h)
        integral_2, _ = quad(integrant_2, q_h, inf)
        integral = integral_1 + integral_2
    return phi + (1 / (1 - c)) * integral

def perf_fct_pr2(phi, q_h, c, mu, sig, p_g, p_f):
    integral = 0;
    dp = p_g + p_f
    
    integrant_1 = lambda q_R : N(q_R,mu,sig)
    integrant_2 = lambda q_R : q_R * N(q_R,mu,sig)
        
    if phi >= 0:
        integral_1, _ = quad(integrant_1, - inf, q_h - phi / dp)
        integral_2, _ = quad(integrant_2, - inf, q_h - phi / dp)
        integral = (q_h - phi / dp) * integral_1 - integral_2
    else:
        integral_1, _ = quad(integrant_1, -inf, q_h)
        integral_2, _ = quad(integrant_2, -inf, q_h)
        integral = q_h * integral_1 - integral_2 - phi / dp
    return phi + (dp / (1 - c)) * integral
    
def perf_fct_num(phi, q_h, c, mu, sig, p_g, p_f):
    ''' Conditional Value at Risk performance function'''
    p = lambda value : max(value, 0)
    loss_fct = lambda q_h, q_r : (p_g + p_f) * p(q_h - q_r)
    integrand = lambda q_r : p(loss_fct(q_h, q_r) - phi) * N(q_r, mu, sig)
    value, _ = quad(integrand, - inf, inf)
    return phi + (1 / (1 - c)) * value

def N(x, mu, sig):
    ''' Normal distribution evaluated at x. '''
    return (1 / (sqrt(2 * pi) * sig)) * exp(- (x - mu)**2 / (2 * sig**2))

def str_value(value):
    return str(value) if isinstance(value, int) else "{:.3}".format(value)

def str_para(q_h, c, mu, sig, p_g, p_f):     
     return str_value(q_h) + " | " + str_value(c) + " | " + str_value(mu) \
         + " | " + str_value(sig) + " | " + str_value(p_g + p_f)
        
q_h = arange(0.0,5.25,0.25)
c = 0.9
c_scn = arange(0.1,1,0.2)
mu = 3
mu_scn = range(-8,8,4)
sig = 1
sig_scn = range(1,6,2)
p_g = 0.5
p_g_scn = arange(0.1,1,0.2)
p_f = 0.1

for para in c_scn:
    y = [slvd_perf_fct(q_h_slct, para, mu, sig, p_g, p_f) for q_h_slct in q_h]
    y_num = [perf_fct_num(minimize_scalar(lambda phi_slct : perf_fct_num(phi_slct, q_h_slct, para, mu, sig, p_g, p_f)).x, q_h_slct, para, mu, sig, p_g, p_f) for q_h_slct in q_h]
    lbl = "c = " + str_value(para)
    lbl_num = "c_{num} = " + str_value(para)
    plt.plot(q_h, y, label=lbl)
    plt.plot(q_h, y_num, '--', label=lbl_num)
plt.xlabel("q^h")
plt.ylabel("CVaR")
plt.legend()
plt.show()

for para in mu_scn:
    y = [slvd_perf_fct(q_h_slct, c, para, sig, p_g, p_f) for q_h_slct in q_h]
    y_num = [perf_fct_num(minimize_scalar(lambda phi_slct : perf_fct_num(phi_slct, q_h_slct, c, para, sig, p_g, p_f)).x, q_h_slct, c, para, sig, p_g, p_f) for q_h_slct in q_h]
    lbl = "mu = " + str_value(para)
    lbl_num = "mu_{num} = " + str_value(para)
    plt.plot(q_h, y, label=lbl)
    plt.plot(q_h, y_num, '--', label=lbl_num)
plt.xlabel("q^h")
plt.ylabel("CVaR")
plt.legend()
plt.show()

for para in sig_scn:
    y = [slvd_perf_fct(q_h_slct, c, mu, para, p_g, p_f) for q_h_slct in q_h]
    y_num = [perf_fct_num(minimize_scalar(lambda phi_slct : perf_fct_num(phi_slct, q_h_slct, c, mu, para, p_g, p_f)).x, q_h_slct, c, mu, para, p_g, p_f) for q_h_slct in q_h]
    lbl = "sig = " + str_value(para)
    lbl_num = "sig_{num} = " + str_value(para)
    plt.plot(q_h, y, label=lbl)
    plt.plot(q_h, y_num, '--', label=lbl_num)
plt.xlabel("q^h")
plt.ylabel("CVaR")
plt.legend()
plt.show()

for para in p_g_scn:
    y = [slvd_perf_fct(q_h_slct, c, mu, sig, para, p_f) for q_h_slct in q_h]
    y_num = [perf_fct_num(minimize_scalar(lambda phi_slct : perf_fct_num(phi_slct, q_h_slct, c, mu, sig, para, p_f)).x, q_h_slct, c, mu, sig, para, p_f) for q_h_slct in q_h]
    lbl = "p_g = " + str_value(para)
    lbl_num = "p_g_{num} = " + str_value(para)
    plt.plot(q_h, y, label=lbl)
    plt.plot(q_h, y_num, '--', label=lbl_num)
plt.xlabel("q^h")
plt.ylabel("CVaR")
plt.legend()
plt.show()


