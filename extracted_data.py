# -*- coding: utf-8 -*-
"""
Created on Mon Aug  9 12:45:13 2021

@author: S3739258
"""

def avg(values):
    return sum(values) / len(values)

class ExtractedData():
    def __init__(self, clock):
        self.clock = clock
        self.tracked_agents = []
        self.time_steps = []
        self.var_assignment = dict()
        self.default_value = []
        self.data = []
    
    def init_tracked_var(self, var_name, default_value):
        if var_name not in self.var_assignment.keys():
            self.var_assignment[var_name] = len(self.data)
            self.default_value.append(default_value)
            self.data.append(list())
        else:
            err_msg = "extractedData.py: Variable {} has already been " \
                + "initialised for tracking!"
            err_msg = err_msg.format(var_name)
            raise RuntimeError(err_msg)
        
    def init_tracked_agent(self, agent_uid):
        tracking_id = len(self.tracked_agents)
        self.tracked_agents.append(agent_uid)
        return tracking_id
    
    def set(self, tracking_id, var_name, value):
        if self.clock.is_pre_heated:
            self.check_if_new_time_step_started()
            self.data[self.var_assignment[var_name]][-1][tracking_id] = value
                
    
    def add(self, tracking_id, var_name, value):
        if self.clock.is_pre_heated:
            self.check_if_new_time_step_started()
            self.data[self.var_assignment[var_name]][-1][tracking_id] += value
    
    def get(self, time_step, tracking_id, var_name):
        var_name_it = self.var_assignment[var_name]
        time_step_it = self.time_steps.index(time_step)
        return self.data[var_name_it][time_step_it][tracking_id]
    
    def tracked_vars(self):
        return list(self.var_assignment.keys())
    
    def tracked_time_steps(self):
        return self.time_steps
                
    def sum_over_time_step(self, var_name, time_step):
        var_name_it = self.var_assignment[var_name]
        time_step_it = self.time_steps.index(time_step)
        return sum([self.data[var_name_it][time_step_it][tracking_id]\
                    for tracking_id in range(self.nbr_of_tracked_agents)])
    
    def sum_over_agent(self, var_name, tracking_id):
        var_name_it = self.var_assignment[var_name]
        return sum([self.data[var_name_it][time_step] \
                    [tracking_id] \
                    for time_step in range(len(self.time_steps))])
    
    def sum_over_all_agents(self, var_name):
        return sum([sum(self.data[self.var_assignment[var_name]][time_step])\
                    for time_step in range(len(self.time_steps))])
    
    def avg_over_agents(self, var_name, time_step):
        var_name_it = self.var_assignment[var_name]
        time_step_it = self.time_steps.index(time_step)
        return avg(self.data[var_name_it][time_step_it])
    
    def avg_over_time_and_agents(self, var_name):
        var_name_it = self.var_assignment[var_name]
        return sum([avg(time_step_data) \
                    for time_step_data \
                    in self.data[var_name_it]])\
               / len(self.time_steps)
               
    def agent_time_series(self, tracking_id, var_name):
        var_name_it = self.var_assignment[var_name]
        return [self.data[var_name_it][time_step][tracking_id]\
                for time_step in range(len(self.time_steps))]
               
    def all_agents_time_series(self, var_name):
        var_name_it = self.var_assignment[var_name]
        return [self.data[var_name_it][time_step]\
                for time_step in range(len(self.time_steps))]
               
    def all_agents_sum_time_series(self, var_name):
        var_name_it = self.var_assignment[var_name]
        return [sum(self.data[var_name_it][time_step]) \
                for time_step in range(len(self.time_steps))]
    def all_agents_avg_time_series(self, var_name):
        var_name_it = self.var_assignment[var_name]
        return [avg(self.data[var_name_it][time_step]) \
                for time_step in range(len(self.time_steps))]
    
    def check_if_new_time_step_started(self):
        new_time_step_start = False
        if len(self.time_steps) == 0:
            new_time_step_start = True
        elif self.time_steps[-1] != self.clock.elapsed_time:
            new_time_step_start = True
            
        if new_time_step_start:
            self.prepare_new_time_step()
    
    def prepare_new_time_step(self):
        self.time_steps.append(self.clock.elapsed_time)
        for var_it, var_data in enumerate(self.data):
            var_data.append(list())
            for agent_it in range(len(self.tracked_agents)):
                var_data[-1].append(self.default_value[var_it])