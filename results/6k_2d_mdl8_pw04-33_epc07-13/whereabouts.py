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
                 location_road_manager, calendar_planner):
        
        self.agent_uid = agent_uid
        self.lrm = location_road_manager
        self.cp = calendar_planner
        self.destination_activity = start_activity
        self.destination_location = start_location
        self.destination_activity_start_time = 0
        self.cur_activity = start_activity
        self.cur_location = start_location
        self.cur_edge = (start_location.uid, start_location.uid)
        self.cur_location_coordinates = self.cur_location.coordinates()
        self.is_travelling = False
        self.has_arrived = True
        self.distance_since_last_location = 0 # in km
        self.route = []
        
    def set_destination(self, destination_activity, destination_location,
                        destination_activity_start_time):
        """
        Sets a new destination and calculates route to get there.
        """
        self.route = self.lrm.calc_route(self.cur_location,
                                         destination_location)
        if len(self.route) >= 2:
            self.cur_edge = (self.route[0], self.route[1])
        else:
            self.cur_edge = (self.route[0], self.route[0])
        self.cur_activity = self.cp.TRANSIT
        self.destination_activity = destination_activity
        self.destination_location = destination_location
        self.destination_activity_start_time = destination_activity_start_time
        self.is_travelling = True
        self.has_arrived = False
        
    def terminate_trip(self, has_arrived):
        """ Aborts the current trip. """
        self.route = []
        self.cur_edge = (self.cur_location.uid, self.cur_location.uid)
        self.is_travelling = False
        self.has_arrived = has_arrived
        self.distance_since_last_location = 0
        if has_arrived:
            self.cur_activity = self.destination_activity
        
    def set_activity_and_location(self, activity, location):
        self.cur_activity = activity
        self.cur_location = location
        self.cur_edge = (location.uid, location.uid)
        self.cur_location_coordinates = location.coordinates()
        self.destination_activity = activity
        self.destination_location = location
        
    
    def __repr__(self):
        act = ["Transit", "Home", "Work", "Emergency"][self.cur_activity]
        msg = "Cur activity: {} ({})), Cur location: {}\n"\
            .format(self.cur_activity, act, self.cur_location)
        msg += "Cur edge: {}, Cur coordinates: {:.04f},{:.04f}\n".format( \
                self.cur_edge, self.cur_location_coordinates[0],
                self.cur_location_coordinates[1])
        msg += "Is traveling: {}, Dist since last loc: {:.03f}\n".format( \
                self.is_travelling, self.distance_since_last_location)
        msg += "Has arrived: {}, ".format(self.has_arrived)
        msg += "Route: " + str(self.route)
        return msg