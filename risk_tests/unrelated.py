# -*- coding: utf-8 -*-
"""
Created on Fri May  7 19:05:31 2021

@author: S3739258
"""

import numpy

def f(m1,m2,v1,v2):
    p = (2*v2-(m1/m2)*v1)/(1+m1/m2)
    q = (m1*v1/m2-2*v2-v1)*v1/(1-m1/m2)
    """
    sqrt= ((v1+v2)/(m2/m1-1))**2-((v1*(-2*v2+v1*(1-m1/m2)))/(1-(m1/m2)))
    frst = (v1+v2)/(m2/m1-1)
    
    a = frst + numpy.sqrt(sqrt)
    b = frst - numpy.sqrt(sqrt)
    """
    return p,q