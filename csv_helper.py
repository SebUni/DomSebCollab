# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 20:00:11 2020

@author: S3739258
"""

import csv
import sys

class CSVHelper():
    """
    Opens a csv file and provides access to its content. First row is treated
    as header!
    """
    def __init__(self, relative_path, filename):
        """
        Parameters
        ----------
        relative_path : string
            E.g.: For "data\file_name.csv" enter "data".
        filename : string
            E.g.: For "data\file_name.csv" enter "file_name.csv".

        Returns
        -------
        Populates self.reader an iteratable object holding the data.

        """
        path_and_file = str(relative_path) + "\\" + str(filename)
        if str(relative_path) == "":
            path_and_file = str(filename)
        # acquire data
        self.data = []
        with open(path_and_file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            next(reader, None) # skip header
            for row in reader:
                self.data.append(row)
        
        # check if data exists
        if len(self.data) == 0:
            msg = str(filename) + " does not contain valid data."
            msg += " First row is header and is skipped!"
            
            sys.exit(msg)