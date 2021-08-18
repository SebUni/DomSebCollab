# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 16:08:47 2021

@author: S3739258
"""

from numpy import sqrt, exp, pi, arange
from scipy.special import erf, erfinv
import matplotlib.pyplot as plt

def q_w_0(q_ow, soc, p_f, p_g, p_w, c, mu, sig):
    q_thresh = mu + sqrt(2) * sig * erfinv(1 - 2 * c)
    p_thresh = p_f \
        + ((p_g - p_f) / (2 * (1 - c))) \
        * (erf((- mu) / (sqrt(2) * sig)) + 1)
    q_0 = 2 * q_ow - soc - mu \
                - sqrt(2) * sig \
                * erfinv(2 * (1 - c) * (p_w - p_f) / (p_g - p_f) - 1)
    if  q_ow < q_thresh:
        if p_w >= p_thresh:
            print(1)
            return q_ow - soc
        elif p_w <= p_thresh:
            print(2)
            return 2 * q_ow - soc
        else:
            print(3)
            return q_0
    elif q_thresh < 0:
        if p_g < p_w:
            print(4)
            return q_ow - soc
        elif p_g > p_w:
            print(5)
            return 2 * q_ow - soc
        else:
            print("a")
            raise RuntimeError("no unique solution for this")
    else:
        if p_w > p_g:
            print(6)
            return q_ow - soc
        elif p_w == p_g:
            print("b")
            raise RuntimeError("no unique solution for this")
        elif p_thresh < p_w < p_g:
            print(7)
            return q_0
        else:
            print(8)
            return 2 * q_ow - soc

def C_deriv(q_w, q_ow, soc, p_f, p_g, p_w, p_em, c, mu, sig):
    if q_w < 2 * q_ow - soc - mu - sqrt(2) * sig *erfinv(1 - 2* c):
        return p_w - p_g
    else:
        return p_w - p_f - ((p_g - p_f)/(2 * (1 - c)))*(erf((2 * q_ow - soc - q_w - mu)/(sqrt(2) * sig)) + 1)

def C_para(q_w, q_ow, soc, p_f, p_g, p_w, p_em, c, mu, sig):
    q_h = max(min(2 * q_ow - soc - q_w, q_ow),0)
    return C(q_h, q_w, q_ow, soc, p_f, p_g, p_w, p_em, c, mu, sig)

def C(q_h, q_w, q_ow, soc, p_f, p_g, p_w, p_em, c, mu, sig):
    C_reg = q_w * p_w + q_h * p_f 
    C_em =  p_em * (p(q_ow - soc - q_w) \
                     + p(q_ow - p(soc + q_w - q_ow) - q_h))
    _CVaR = CVaR(2 * q_ow - soc - q_w, c, mu, sig, p_g, p_f)
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
q_h = 2
q_h_scn = range(0,q_ow,2)

step = 0.01
q_w = arange(q_ow - soc,2 * q_ow - soc + step, step)
c = 0.5
c_scn = arange(0.1,1,0.4)
mu = 0
mu_scn = range(-8,8,4)
sig = 1
sig_scn = range(1,6,2)
p_g = 0.55
p_g_scn = arange(0.1,1,0.2)
p_w = 0.5
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
    C_q_w = [C_para(q_w_slct, q_ow, soc, p_f, p_g, p_w, p_em, para, mu, sig) for q_w_slct in q_w]
    C_deriv_q_w = [C_deriv(q_w_slct, q_ow, soc, p_f, p_g, p_w, p_em, para, mu, sig) for q_w_slct in q_w]
    # CVaR_q_h = [CVaR(q_h_slct, para, mu, sig, p_g, p_f) for q_h_slct in q_h]
    print("q_w_0(c = " + str_value(para) + ") = " + str_value(q_w_0(q_ow, soc, p_f, p_g, p_w, para, mu, sig)))
    #print("Root: " + str_value(q_h_0(q_h, q_ow, soc, p_f, p_g, p_w, para, mu, sig)))
    #print("Threshold: " + str_value(mu + sqrt(2) * sig * erfinv(1-2*para))) 
    lbl = "c = " + str_value(para)
    lbl_deriv = "c_deriv = " + str_value(para)
    plt.plot(q_w, C_q_w, label=lbl)
    #plt.plot(q_w, C_deriv_q_w, label=lbl_deriv)
plt.xlabel("q^h")
plt.ylabel("C(q^w)")
plt.legend()
plt.show()
