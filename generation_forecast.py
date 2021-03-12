# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 23:13:14 2021

@author: S3739258
"""

import numpy

from cast import Cast

class GenerationForecast():
    def __init__(self, clock, row):
        time_factor = 60 // clock.time_step
        time_factor_sqrt = numpy.sqrt(time_factor)
        if 60 % clock.time_step != 0:
            raise RuntimeError("time_step do not add up to full hour!")
        cast = Cast("Normed rooftop PV output fit parameters")
        self.max_output \
            = cast.to_positive_int(row[1], "Max output") / time_factor
        # x_border seperates the part fitted by a constant and the part
        # fitted by a gaussian
        self.x_border = cast.to_positive_int(row[2], "x_border") / time_factor
        self.A = cast.to_positive_float(row[3], "A")
        self.mu = cast.to_positive_int(row[4], "mu") / time_factor
        self.sig = cast.to_positive_float(row[5], "sig") / time_factor_sqrt
        self.y0 = cast.to_positive_float(row[6], "y0")
        self.A_po = cast.to_positive_float(row[7], "A_po")
        self.mu_po = cast.to_positive_int(row[8], "mu_po") / time_factor
        self.sig_po\
            = cast.to_positive_float(row[9], "sig_po") / time_factor_sqrt
        self.y_co = cast.to_positive_float(row[10], "y_co")
        self.surf_po = cast.to_positive_float(row[11], "surf_po")
        self.surf_co = cast.to_positive_float(row[12], "surf_co")
        
    def peak_dominates_constant(self):
        # true if surf_po (surface peak only) > surf_co (surface constant only)
        return (self.surf_po > self.surf_co)