# -*- coding: utf-8 -*-
"""
Created on Tue Aug 10 19:49:46 2021

@author: S3739258
"""

import os
import psutil

class MemoryTracker():
    def __init__(self):
        self.RAM = dict()
    
    def track_now(self, snap_shot_title):
        process = psutil.Process(os.getpid())
        if snap_shot_title in self.RAM:
            raise RuntimeError("memory_tracker.py: snap_shot_title was "\
                               + "tracked already!")
        self.RAM[snap_shot_title] \
            = (process.memory_info()[0], process.memory_info()[1])
            
    def difference(self, snap_shot_title_before, snap_shot_title_after):
        if not (snap_shot_title_before in self.RAM \
                and snap_shot_title_after in self.RAM):
            raise RuntimeError("memory_tracker.py: Snap shot titles do not "\
                               + "exist!")
        mem = (self.RAM[snap_shot_title_after][0] \
               - self.RAM[snap_shot_title_before][0]) / float(2 ** 20)
        vmem = (self.RAM[snap_shot_title_after][1] \
               - self.RAM[snap_shot_title_before][1]) / float(2 ** 20)
        return "{:.00f} MB".format(mem + vmem)
        
    def absolute(self, snap_shot_title):
        if not snap_shot_title in self.RAM:
            raise RuntimeError("memory_tracker.py: Snap shot title does not "\
                               + "exist!")
        mem = self.RAM[snap_shot_title][0]  / float(2 ** 20)
        vmem = self.RAM[snap_shot_title][1] / float(2 ** 20)
        return "{:.00f} MB".format(mem + vmem)