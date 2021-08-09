# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 12:46:02 2021

@author: S3739258
"""

import sys
import datetime
import time
import logging

def seconds_to_time_string(seconds):
    eta_sec = int(seconds % 60)
    eta_min = int((seconds // 60) % 60)
    eta_hour = int(seconds // (60 * 60))
    
    time_str_overtime = "> 999h 59m 59s"
    
    time_str = ""
    if eta_hour != 0:
        time_str += "{:02d}h ".format(eta_hour)
    if eta_hour != 0 or eta_min != 0:
        time_str += "{:02d}m ".format(eta_min)
    time_str += "{:02d}s".format(eta_sec)
    
    if seconds >= 1000 * 60 * 60 :
        time_str = time_str_overtime
        
    time_str += " " * (len(time_str_overtime) - len(time_str))
    
    return time_str

class ConsoleOutput():
    def __init__(self):
        self.limits = dict()
        self.start_time = dict()
        self.PROGRESS_BAR_LENGTH = 30
        self.clean_logger()
        path = "results/"
        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path_filename = path + filename + ".log"
        logging.basicConfig(filename=path_filename, level=logging.INFO)
    
    # time print
    def t_print(self, message):
        time_str = datetime.datetime.now().strftime("[%H:%M:%S]")
        final_msg = "{} {}".format(time_str, message)
        logging.info(final_msg)
        print(final_msg)
        
    # indent print
    def i_print(self, message):
        print("           " + message)
        
    def startProgress(self, title, start_value, limit):
        self.limits[title] = limit
        self.start_time[title] = time.time()
        sys.stdout.write(" ")
        sys.stdout.flush()
        self.progress(title, start_value)
    
    def progress(self, title, cur_value):
        cur_rel_value = cur_value / self.limits[title]
        int_progress = int(self.PROGRESS_BAR_LENGTH * cur_rel_value)
        progress_characters \
            = "[" + ("#" * int_progress) \
                + (" " * (self.PROGRESS_BAR_LENGTH - int_progress)) + "]"
        time_str = datetime.datetime.now().strftime("[%H:%M:%S]")
        eta_str = "?"
        if cur_rel_value != 0:
            eta = (time.time() - self.start_time[title]) * (1 - cur_rel_value)\
                / cur_rel_value
            eta_str = seconds_to_time_string(eta)
        full_line =  "{} {} {} / {} | ETA {}".format(time_str,
            progress_characters, cur_value, self.limits[title], eta_str)
        sys.stdout.write("\r{}".format(full_line))
        sys.stdout.flush()
    
    def endProgress(self, title, message):
        eta_l = len(" | ETA > 999h 59m 59s")
        clean_line = " " * (11+1+40+1+1+len(str(self.limits[title]))*2+3+eta_l)
        sys.stdout.write("\r{}".format(clean_line))
        sys.stdout.flush()
        time_str = datetime.datetime.now().strftime("[%H:%M:%S]")
        sys.stdout.write("\r{} {}\n".format(time_str, message))
        sys.stdout.flush()
        logging.info("{} {}".format(time_str, message))
        del self.limits[title]
        del self.start_time[title]
        
    def clean_logger(self):
        for handler in logging.root.handlers:
            logging.root.removeHandler(handler)