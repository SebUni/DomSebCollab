# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 16:08:47 2021

@author: S3739258
"""

from numpy import sqrt, exp, pi, arange
from scipy.special import erf, erfinv
import matplotlib.pyplot as plt

def q_h_0(q_h, q_ow, soc, p_f, p_g, p_w, c, mu, sig):
    if mu + sqrt(2) * sig * erfinv(1 - 2 * c) < q_ow - soc:
        if p_g < p_w:
            print(1)
            return 2 * q_ow - soc
        elif p_g > p_w:
            print(2)
            return q_ow - soc
        else:
            print("a")
            raise RuntimeError("no unique solution for this")
    elif 2*q_ow - soc < mu + sqrt(2) * sig * erfinv(1 - 2 * c):
        if p_w <= p_f + ((p_g - p_f)/(2 * (1 - c)))*(erf((q_ow - soc - mu)/(sqrt(2) * sig))+1):
            print(3)
            return q_ow - soc
        elif p_w >= p_f + ((p_g - p_f)/(2 * (1 - c)))*(erf((2* q_ow - soc - mu)/(sqrt(2) * sig))+1):
            print(4)
            return 2 * q_ow - soc
        else:
            print(5)
            return sqrt(2) * sig * erfinv(2 * (1 - c) * (p_w - p_f) / (p_g - p_f) - 1) + mu
    else:
        if p_w <= p_f + ((p_g - p_f)/(2 * (1 - c)))*(erf((q_ow - soc - mu)/(sqrt(2) * sig))+1):
            print(6)
            return q_ow - soc
        elif p_f + ((p_g - p_f)/(2 * (1 - c)))*(erf((q_ow - soc - mu)/(sqrt(2) * sig))+1) < p_w < p_g:
            print(7)
            return sqrt(2) * sig * erfinv(2 * (1 - c) * (p_w - p_f) / (p_g - p_f) - 1) + mu
        elif p_w == p_g:
            print("b")
            raise RuntimeError("no unique solution for this")
        else:
            return 2 * q_ow - soc

def C_deriv(q_h, q_ow, soc, p_f, p_g, p_w, p_em, c, mu, sig):
    if q_h > mu + sqrt(2) * sig *erfinv(1 - 2* c):
        return p_g - p_w
    else:
        return p_f - p_w + ((p_g - p_f)/(2 * (1 - c)))*(erf((q_h - mu)/(sqrt(2) * sig)) + 1)

def C_para(q_h, q_ow, soc, p_f, p_g, p_w, p_em, c, mu, sig):
    q_w = max(min(2 * q_ow - soc - q_h, q_ow),0)
    return C(q_h, q_w, q_ow, soc, p_f, p_g, p_w, p_em, c, mu, sig)

def C(q_h, q_w, q_ow, soc, p_f, p_g, p_w, p_em, c, mu, sig):
    C_reg = q_w * p_w + q_h * p_f 
    C_em =  p_em * (p(q_ow - soc - q_h) \
                     + p(q_ow - p(soc + q_h - q_ow) - q_w))
    _CVaR = CVaR(q_h, c, mu, sig, p_g, p_f)
    return C_reg + C_em + _CVaR

def p(value):
    return max(value,0)

def CVaR(q_h, c, mu, sig, p_g, p_f):
    dp = p_g - p_f
    phi_0 = root_analytic(q_h, c, mu, sig, p_g, p_f)
    psi = q_h - mu - phi_0 / dp
    return dp * (q_h - psi - mu + (1 / (1 - c)) \
        * ((psi / 2) * (erf(psi/(sqrt(2) * sig))+1) + sig**2 * N(psi, 0, sig)))

def root_analytic(q_h, c, mu, sig, p_g, p_f):
    dp = p_g - p_f
    return max(dp * (q_h - mu - sqrt(2) * sig * erfinv(1 - 2 * c)), 0.0)

def N(x, mu, sig):
    ''' Normal distribution evaluated at x. '''
    return (1 / (sqrt(2 * pi) * sig)) * exp(- (x - mu)**2 / (2 * sig**2))

def str_value(value):
    return str(value) if isinstance(value, int) else "{:.3}".format(value)

def str_para(q_h, c, mu, sig, p_g, p_f):     
     return str_value(q_h) + " | " + str_value(c) + " | " + str_value(mu) \
         + " | " + str_value(sig) + " | " + str_value(p_g + p_f)

q_ow = 10
soc = 2
q_w = 2
q_w_scn = range(0,q_ow,2)

step = 0.1
q_h = arange(q_ow - soc,2 * q_ow - soc + step, step)
c = 0.5
c_scn = arange(0.1,1,0.4)
mu = 15
mu_scn = range(-8,8,4)
sig = 1
sig_scn = range(1,6,2)
p_g = 0.5
p_g_scn = arange(0.1,1,0.2)
p_w = 0.4 
p_f = 0.1
p_em = 2

# # with q_h and q_w considered independent
# for para in q_w_scn:
#     C_q_h = [C(q_h_slct, para, q_ow, soc, p_f, p_g, p_w, p_em, c, mu, sig) for q_h_slct in q_h]
#     lbl = "q_w = " + str_value(para)
#     plt.plot(q_h, C_q_h, label=lbl)
# plt.xlabel("q^h")
# plt.ylabel("C(q^h)")
# plt.legend()
# plt.show()

# with q_h and q_w considered dependent
for para in c_scn:
    C_q_h = [C_para(q_h_slct, q_ow, soc, p_f, p_g, p_w, p_em, para, mu, sig) for q_h_slct in q_h]
    C_deriv_q_h = [C_deriv(q_h_slct, q_ow, soc, p_f, p_g, p_w, p_em, para, mu, sig) for q_h_slct in q_h]
    # CVaR_q_h = [CVaR(q_h_slct, para, mu, sig, p_g, p_f) for q_h_slct in q_h]
    # print("q_h_0(c = " + str_value(para) + ") = " + str_value(q_h_0(q_h, q_ow, soc, p_f, p_g, p_w, para, mu, sig)))
    print("Root: " + str_value(q_h_0(q_h, q_ow, soc, p_f, p_g, p_w, para, mu, sig)))
    print("Threshold: " + str_value(mu + sqrt(2) * sig * erfinv(1-2*para))) 
    lbl = "c = " + str_value(para)
    lbl_deriv = "c_deriv = " + str_value(para)
    plt.plot(q_h, C_q_h, label=lbl)
    plt.plot(q_h, C_deriv_q_h, label=lbl_deriv)
plt.xlabel("q^h")
plt.ylabel("C(q^h)")
plt.legend()
plt.show()
