# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 13:06:27 2020

@author: S3739258
"""
from mesa import Agent

class CarAgent(Agent):
    """An agent which can travel along the map."""
    def __init__(self, uid, model, cur_location, house_agent, company,
                 car_model_manager, whereabouts_manager):
        """
        Parameters
        ----------
        uid : int
            Unique of the car agent.
        model : ChargingModel
            The base charging model defined as base for the simulation.
        house_agent : HouseAgent
            The house_agent assigned to this car_agent.
        company : Company
            The company where this agent is working.
        car_model_manager : CarModelManager
            The object handling all car models created in ChargingModel class
        whereabouts_manager : WhereaboutsManager
            The object handling all whereabouts created in ChargingModel class

        Returns
        -------
        None.
        """
        super().__init__(uid, model)
        # uid is redundant because super alreay incorperates unique_id but
        # for brevity and consistency through out the code i define uid
        self.uid = uid 
        self.house_agent = house_agent
        self.company = company
        # TODO reconsider how car models are chosen
        self.car_model = car_model_manager.draw_car_model_at_random()
        self.whereabouts = whereabouts_manager.track_new_agent(uid,
                                                               cur_location)
         # TODO check if all agents should start with 100% SOC
        self.soc = 100.0
        
    def step(self):
        self.move()
        
    def move(self):
        new_position = self.model.wm.whereabouts[self.uid].cur_location_coordinates
        self.model.grid.move_agent(self, new_position)