# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 20:09:40 2021

@author: S3739258
"""

import sys

from cast import Cast
from csv_helper import CSVHelper

class Parameters():
    """
    This object provides all user defined parameters not given as an argument
    to charging model. Key-value pairs are stored in "parameters.csv".
    """
    def __init__(self):
        self.parameters = dict()
        file_name = "parameters.csv"
        csv_helper = CSVHelper("data",file_name)        
        for row in csv_helper.data:
            key = row[0]
            value = row[1]
            if key in self.parameters:
                sys.exit("Parameter " + key \
                         + " is defined twice in parameters.csv")
            self.parameters[key] = value
        self.uid_to_check = -1
        self.next_stop = -1
    
    def get_parameter(self, parameter_name, parameter_type):
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
            sys.exit("No parameter called " + parameter_name \
                     + " is defined in parameters.csv")
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
        