# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 15:36:10 2021

@author: S3739258
"""

import multiprocessing

from test_mp_module import TestMpModule
            
if __name__ == "__main__":
    
    name_guard = "parent_module_name" # insert __name__ here
    test = TestMpModule()
    test.do(name_guard)