# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 12:46:02 2021

@author: S3739258
"""

import datetime

class ConsoleOutput():
    def __init__(self):
        pass
    
    # time print
    def t_print(self, message):
        time_str = datetime.datetime.now().strftime("[%H:%M:%S]")
        print(time_str + " " + message)
        
    # indent print
    def i_print(self, message):
        print("           " + message)