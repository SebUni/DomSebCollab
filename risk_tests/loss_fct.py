# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 23:11:54 2021

@author: S3739258
"""

from numpy import pi, sqrt, exp, arange
from scipy.special import erfinv
import matplotlib.pyplot as plt

mu, sig = 5, 1
dp = 1
c = 0.9
q = 1

phi = arange (-15,15,0.1)

def N(x, mu, sig):
    ''' Normal distribution evaluated at x. '''
    return (1 / (sqrt(2 * pi) * sig)) * exp(- (x - mu)**2 / (2 * sig**2))

phi_0_pos = lambda phi : - dp * (sqrt(2) * sig * erfinv(1 - 2 * c) + mu - q)
phi_0_neg = lambda phi : dp * c + phi * N (- phi / dp, mu - q, sig)

y_neg = [phi_0_neg(phi_slct) for phi_slct in phi]

plt.plot(phi, y_neg)
plt.show()