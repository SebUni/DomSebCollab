# -*- coding: utf-8 -*-
"""
Created on Tue Dec  1 16:20:06 2020

@author: S3739258
""" 

class Whereabouts():
    """
    Provides information on the current position of the agent.
    
    This class calculates the progress of travels and feeds information on the
    geographic whereabouts of the agent to the charging model.
    """
    def __init__(self, agent_uid, start_activity, start_location,
                 location_road_manager, calendar_planner, time_step):
        
        self.agent_uid = agent_uid
        self.lrm = location_road_manager
        self.cp = calendar_planner
        self.time_step = time_step
        self.cur_activity = start_activity
        self.cur_location = start_location
        self.cur_edge = (start_location.uid, start_location.uid)
        self.cur_location_coordinates = self.cur_location.coordinates()
        self.is_travelling = False
        self.distance_since_last_location = 0 # in km
        self.route = []
        
    def set_destination(self, destination_location):
        """
        Sets a new destination and calculates route to get there.
        """
        self.route = self.lrm.calc_route(self.cur_location,
                                         destination_location)
        if len(self.route) >= 2:
            route = self.route
            self.cur_edge = (self.route[0], self.route[1])
        else:
            self.cur_edge = (self.route[0], self.route[0])
        self.is_travelling = True
        
    def terminate_trip(self):
        """ Aborts the current trip. """
        self.route = []
        self.cur_edge = (self.cur_location, self.cur_location)
        self.is_travelling = False
        self.distance_since_last_location = 0
    
    def __repr__(self):
        msg = "Current location Uid: " + str(self.cur_location_uid) + "\n"
        msg += "Current edge: " + str(self.cur_edge) + "\n"
        msg += "Time step duration: " + str(self.time_step_duration) + "\n"
        msg += "Current coordinates: "
        msg += str(self.cur_location_coordinates[0]) + " "
        msg += str(self.cur_location_coordinates[1]) + "\n"
        msg += "Is traveling: " + str(self.is_travelling) + "\n"
        msg += "Distance travelled: " + str(self.distance_travelled) + "\n"
        msg += "Route: " + str(self.route)
        return msg