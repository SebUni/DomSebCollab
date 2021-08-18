# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 17:36:22 2021

@author: S3739258
"""

import concurrent.futures

def test_fct(i):
    return i
    
class TestMpModule():
    def __init__(self, name_guard):
        self.name_guard = name_guard
                
    def do(self):
        para = [1, 2, 3]
        if self.name_guard == 'parent_module_name': # check parent module name here
            with concurrent.futures.ProcessPoolExecutor() as executor:
                results = executor.map(test_fct, para)
                
                for result in results:
                    print(result)   
        
        
        
            