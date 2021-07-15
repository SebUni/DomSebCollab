# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 15:01:29 2021

@author: S3739258
"""

import os
import matplotlib.pyplot as plt

def time_stamp(i, time_step):
    days = i * time_step // 60 // 24
    day_of_week = round(int(days % 7)+1)
    hours = i * time_step // 60
    hour_of_day = round(int(hours % 24))
    minutes = round(int(i * time_step - hours * 60))
    return "{:d}d {:02d}h {:02d}m".format(day_of_week, hour_of_day, minutes)

class OutputData():
    def __init__(self, parameters):
        self.parameters = parameters

    def draw_car_agents(self, model, it):
        size = 20
        x_agents = []
        y_agents = []
        for boid in model.schedule_cars.agents:
            x_agent, y_agent = boid.pos
            x_agents.append(x_agent)
            y_agents.append(y_agent)
        x_locations = []
        y_locations = []
        for location in model.lrm.locations.values():
            x_location, y_location = model.lrm.relative_location_position(location)
            x_locations.append(x_location)
            y_locations.append(y_location)
        fig = plt.figure(figsize=(13,13))
        ax = fig.add_subplot(111)
        
        ax.scatter(x_agents, y_agents, s=size)
        ax.scatter(x_locations, y_locations, s=size*1.5, c="r")
        ax.margins(0.1)
        time_step = self.parameters.get_parameter("time_step","int")
        ax.text(0, 0, time_stamp(it, time_step), fontsize=24)
        ax.axis('off')
        title = "{:06d}".format(it) + ".png"
        fig.savefig(title, bbox_inches='tight', pad_inches=0)
        
        # pngs to gif using cmd "magick convert -delay 1 -loop 0 *.png animation.gif"
        # do not connect more than a day
        # overlay gif with map using cmd "magick convert output.gif -layers optimize result.gif"
        # concatenate mutiple using cmd "magick convert day*_map_opt.gif week.gif"
        
    def write_all_to_file(self, model):
        data_file = "output_car_data.csv"
        data_elements_per_agent \
            = list(next(iter(next(iter(model.extracted_data.values())).values())).keys())
        
        if os.path.exists(data_file): os.remove(data_file)
        f = open(data_file,"x")
            
        data_header = "Elapsed time"
        for i in range(model.num_agents):
            for element in data_elements_per_agent:
                data_header += "," + str(element)
        f.writelines(data_header + "\n")
        
        for time_step, time_step_data in model.extracted_data.items():
            line = str(time_step)
            for agent_data in time_step_data.values():
                for element in data_elements_per_agent:
                    line += "," + str(agent_data[element])
            f.writelines(line + "\n")
        f.close()
        
    def write_one_agent_to_file(self, model, agent_uid):
        data_elements_per_agent \
            = list(next(iter(next(iter(model.extracted_data.values())).values())).keys())
        out = []
        out.append("time_step," + ",".join(data_elements_per_agent))
        for time_step, data in model.extracted_data.items():
            line = str(time_step)
            for elem in data_elements_per_agent:
                if isinstance(data[agent_uid][elem], int):
                    line += ",{}".format(data[agent_uid][elem])
                else:
                    line += ",{:.03f}".format(data[agent_uid][elem])
            out.append(line)
        data_file = "output.csv"
        if os.path.exists(data_file): os.remove(data_file)
        f = open(data_file,"x")
        for line in out:
            f.writelines(line + "\n")
        f.close()
        
    def plot_extracted_data(self, model):
        time_steps = [time_step for time_step in model.extracted_data.keys()]
        data_elements_per_agent \
            = list(next(iter(next(iter(model.extracted_data.values())).values())).keys())
        
        for element in data_elements_per_agent:
            fig, ax = plt.subplots()
            for agent in next(iter(model.extracted_data.values())):
                soc = [time_step[agent][element] for time_step in model.extracted_data.values()]
                ax.plot(time_steps, soc)
            ax.set(xlabel='time in minutes', ylabel=element)
            plt.show()
            
    def print_overall_charging_results(self, model):
        total_charge = model.total_charge()
        print("Charge: @home = {}, @work = {}, @emergency = {},".format(total_charge["home"],
                                                                        total_charge["work"],
                                                                        total_charge["emergency"]))
        print("Company Charger Utilisation: {}".format(model.lrm.average_company_charger_utilisation()))