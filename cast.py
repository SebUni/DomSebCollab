# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 15:13:20 2020

@author: S3739258
"""

import sys

class Cast():
    def __init__(self, object_name):
        self.object_name = object_name
        self.uid = None
        
    def to_float(self, var_input, var_title):
        try:
           output = float(var_input)
        except ValueError:
            sys.exit(var_title + " of " + self.object_name + " " 
                     + str(self.uid) + " is ill defined!")
        
        return output
    
    def to_positive_float(self, var_input, var_title):
        output = self.to_float(var_input, var_title)
        if output < 0:
            sys.exit(var_title + " of " + self.object_name + " " 
                     + str(self.uid) + " is ill defined!")
        
        return output
        
    def to_int(self, var_input, var_title):
        try:
           output = int(var_input)
        except ValueError:
            sys.exit(var_title + " of " + self.object_name + " " 
                     + str(self.uid) + " is ill defined!")
        
        return output
    
    def to_positive_int(self, var_input, var_title):
        output = self.to_int(var_input, var_title)
        if output < 0:
            sys.exit(var_title + " of " + self.object_name + " " 
                     + str(self.uid) + " is ill defined!")
        
        return output