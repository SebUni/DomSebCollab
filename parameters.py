# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 20:09:40 2021

@author: S3739258
"""

import sys
import datetime

from cast import Cast
from csv_helper import CSVHelper

class Parameters():
    """
    This object provides all user defined parameters not given as an argument
    to charging model. Key-value pairs are stored in "parameters.csv".
    """
    def __init__(self):
        self.OVERWRITE_STATISTIC = "STATISTIC"
        self.OVERWRITE_TRUE = "TRUE"
        self.OVERWRITE_FALSE = "FALSE"
        
        self.parameters = dict()
        file_name = "parameters.csv"
        csv_helper = CSVHelper("data",file_name)        
        for row in csv_helper.data:
            key = row[0]
            value = row[1]
            if key in self.parameters:
                raise RuntimeError("parameters.py: Parameter " + key \
                                   + " is defined twice in parameters.csv")
            self.parameters[key] = value
        self.uid_to_check = -1
        self.next_stop = -1
        self.result_path = "results/"
        self.file_name_prefix = "model_{}_nbr_agents_{}_season_{}_".format(\
                                        self.parameters["charging_model"],
                                        self.parameters["nbr_of_agents"],
                                        self.parameters["season"])
        if self.parameters["file_name_prefix_addendum"] != "":
            self.file_name_prefix \
                += self.parameters["file_name_prefix_addendum"] + "_"
    
    def get(self, parameter_name, parameter_type):
        """
        Returns a parameter from self.parameter as a requested type.

        Parameters
        ----------
        parameter_name : string
            Name of the parameter requested.
        parameter_type : string
            Type the parameter is requested in. Currently    
            supported: float, positive_float, int, positive_int, string,
            boolean.

        Returns
        -------
        <Type as requested in parameter_type>
            Well the parameter request casted as the type requested

        """
        if parameter_name not in self.parameters:
            raise RuntimeError("parameters.py: No parameter called " \
                               +parameter_name+" is defined in parameters.csv")
        value_str = self.parameters[parameter_name]
        
        cast = Cast("Get Parameter")
        if parameter_type == "float":
            return cast.to_float(value_str, parameter_name)
        elif parameter_type == "positive_float":
            return cast.to_positive_float(value_str, parameter_name)
        elif parameter_type == "int":
            return cast.to_int(value_str, parameter_name)
        elif parameter_type == "positive_int":
            return cast.to_positive_int(value_str, parameter_name)
        elif parameter_type == "string":
            return value_str
        elif parameter_type == "boolean":
            return cast.to_boolean(value_str, parameter_name)
        else:
            sys.exit("Type '" + parameter_type + "' for parameter " \
                     + parameter_name + " is not recognised")
                
    def overwrite_value(self, parameter_name):
        overwrite_value = self.get(parameter_name, "string")
        if overwrite_value not in [self.OVERWRITE_STATISTIC,
                                   self.OVERWRITE_TRUE,
                                   self.OVERWRITE_FALSE]:
            raise RuntimeError("parameters.py: Overwrite parameter " \
                               + parameter_name + "is ill defined!")
        return overwrite_value
    
    def overwrite(self, parameter_name, original_value=None):
        overwrite_value = self.overwrite_value(parameter_name)
        
        if not isinstance(original_value, bool) and not original_value == None:
            raise RuntimeError("parameters.py: Original value to overwrite "\
                               + "for " + parameter_name + " is not a bool!")
        if original_value == None \
            and overwrite_value == self.OVERWRITE_STATISTIC:
            raise RuntimeError("parameters.py: No original value provided "\
                               + "and overwrite value 'statistic' chosen for "\
                               + parameter_name)
                
        if overwrite_value == self.OVERWRITE_STATISTIC:
            return original_value
        elif overwrite_value == self.OVERWRITE_TRUE:
            return True
        else:
            return False
        
    def path_file_name(self, identifier, ending,
                       pf_name_wo_identifier_and_ending=""):
        if pf_name_wo_identifier_and_ending == "":
            return self.result_path + self.file_name_prefix + str(identifier) \
                + str(ending)
        else:
            return pf_name_wo_identifier_and_ending + str(identifier) \
                + str(ending)
        