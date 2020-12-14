# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 13:06:27 2020

@author: S3739258
"""

from mesa import Agent

class CarAgent(Agent):
    """An agent which can travel along the map."""
    def __init__(self, uid, model, house_agent, company, car_model,
                 whereabouts):
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
        car_model : CarModel
            The car model this car agent is utilising.
        whereabouts : Whereabouts
            The whereabouts class tracking this agent's position and movement.

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
        self.car_model = car_model
        self.whereabouts = whereabouts
        self.soc = 100.0 # TODO check if all agents should start with 100% SOC
        
    def step(self):
        self.move()
        
    def move(self):
        new_position = self.model.wm.whereabouts[self.uid].cur_location_coordinates
        self.model.grid.move_agent(self, new_position)