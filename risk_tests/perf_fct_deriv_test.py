# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 16:08:47 2021

@author: S3739258
"""

from numpy import sqrt, exp, pi, arange, gradient
from scipy.special import erf, erfinv
import matplotlib.pyplot as plt

def root_analytic(q_h, c, mu, sig, p_g, p_f):
    dp = p_g + p_f
    return max(dp * (q_h - mu - sqrt(2) * sig * erfinv(1 - 2 * c)), 0.0)

def CVaR(q_h, c, mu, sig, p_g, p_f):
    dp = p_g + p_f
    phi_0 = root_analytic(q_h, c, mu, sig, p_g, p_f)
    psi = q_h - mu - phi_0 / dp
    return dp * (q_h - psi - mu + (1 / (1 - c)) \
        * ((psi / 2) * (erf(psi/(sqrt(2) * sig))+1) + sig**2 * N(psi, 0, sig)))
        
def CVaR_deriv(q_h, c, mu, sig, p_g, p_f):
    dp = p_g + p_f
    return dp*(1+((1/(2*(1-c)))*(erf((q_h-mu)/(sqrt(2)*sig))+1)-1)*(q_h <= mu + sqrt(2)*sig*erfinv(1-2*c)))

def N(x, mu, sig):
    ''' Normal distribution evaluated at x. '''
    return (1 / (sqrt(2 * pi) * sig)) * exp(- (x - mu)**2 / (2 * sig**2))

def str_value(value):
    return str(value) if isinstance(value, int) else "{:.3}".format(value)

def str_para(q_h, c, mu, sig, p_g, p_f):     
     return str_value(q_h) + " | " + str_value(c) + " | " + str_value(mu) \
         + " | " + str_value(sig) + " | " + str_value(p_g + p_f)

q_h = arange(0.0,5.1,0.1)
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
    f_q_h = [CVaR(q_h_slct, para, mu, sig, p_g, p_f) for q_h_slct in q_h]
    y_ana = [CVaR_deriv(q_h_slct, para, mu, sig, p_g, p_f) for q_h_slct in q_h]
    y_num = gradient(f_q_h, q_h)
    lbl = "c = " + str_value(para)
    lbl_num = "c_{num} = " + str_value(para)
    plt.plot(q_h, y_ana, label=lbl)
    plt.plot(q_h, y_num, '--', label=lbl_num)
plt.xlabel("q^h")
plt.ylabel("d/dq^h CVaR")
plt.legend()
plt.show()

for para in mu_scn:
    f_q_h = [CVaR(q_h_slct, c, para, sig, p_g, p_f) for q_h_slct in q_h]
    y_ana = [CVaR_deriv(q_h_slct, c, para, sig, p_g, p_f) for q_h_slct in q_h]
    y_num = gradient(f_q_h, q_h)
    lbl = "mu = " + str_value(para)
    lbl_num = "mu_{num} = " + str_value(para)
    plt.plot(q_h, y_ana, label=lbl)
    plt.plot(q_h, y_num, '--', label=lbl_num)
plt.xlabel("q^h")
plt.ylabel("d/dq^h CVaR")
plt.legend()
plt.show()

for para in sig_scn:
    f_q_h = [CVaR(q_h_slct, c, mu, para, p_g, p_f) for q_h_slct in q_h]
    y_ana = [CVaR_deriv(q_h_slct, c, mu, para, p_g, p_f) for q_h_slct in q_h]
    y_num = gradient(f_q_h, q_h)
    lbl = "sig = " + str_value(para)
    lbl_num = "sig_{num} = " + str_value(para)
    plt.plot(q_h, y_ana, label=lbl)
    plt.plot(q_h, y_num, '--', label=lbl_num)
plt.xlabel("q^h")
plt.ylabel("d/dq^h CVaR")
plt.legend()
plt.show()

for para in p_g_scn:
    f_q_h = [CVaR(q_h_slct, c, mu, sig, para, p_f) for q_h_slct in q_h]
    y_ana = [CVaR_deriv(q_h_slct, c, mu, sig, para, p_f) for q_h_slct in q_h]
    y_num = gradient(f_q_h, q_h)
    lbl = "p_g = " + str_value(para)
    lbl_num = "p_g_{num} = " + str_value(para)
    plt.plot(q_h, y_ana, label=lbl)
    plt.plot(q_h, y_num, '--', label=lbl_num)
plt.xlabel("q^h")
plt.ylabel("d/dq^h CVaR")
plt.legend()
plt.show()