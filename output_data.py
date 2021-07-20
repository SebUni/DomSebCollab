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

def time_axis_labels(time_steps):
    max_labels = 22
    total_hours = len(time_steps) // 12
    hour_lbl_step = total_hours // max_labels
    if hour_lbl_step > 24:
        hour_lbl_step = 24
    while 24 % hour_lbl_step != 0:
        hour_lbl_step += 1
    lbl_time_steps, lbl_hour_steps = [], []
    for time_step in time_steps:
        if time_step % 12 == 0:
            hour = time_step // 60 % 24
            if hour % hour_lbl_step == 0:
                lbl_time_steps.append(time_step)
                lbl_hour_steps.append(hour)
    
    return lbl_time_steps, lbl_hour_steps
    

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
        extr_data = model.extracted_car_data
        data_file = "output_car_data.csv"
        data_elements_per_agent \
            = list(next(iter(next(iter(extr_data.values())).values())).keys())
        
        if os.path.exists(data_file): os.remove(data_file)
        f = open(data_file,"x")
            
        data_header = "Elapsed time"
        for i in range(model.num_agents):
            for element in data_elements_per_agent:
                data_header += "," + str(element)
        f.writelines(data_header + "\n")
        
        for time_step, time_step_data in extr_data.items():
            line = str(time_step)
            for agent_data in time_step_data.values():
                for element in data_elements_per_agent:
                    line += "," + str(agent_data[element])
            f.writelines(line + "\n")
        f.close()
        
    def write_one_agent_to_file(self, model, agent_uid):
        extr_data = model.extracted_car_data
        data_elements_per_agent \
            = list(next(iter(next(iter(extr_data.values())).values())).keys())
        out = []
        out.append("time_step," + ",".join(data_elements_per_agent))
        for time_step, data in extr_data.items():
            line = str(time_step)
            for elem in data_elements_per_agent:
                if isinstance(data[agent_uid][elem], int):
                    line += ",{}".format(data[agent_uid][elem])
                else:
                    line += ",{:.03f}".format(data[agent_uid][elem])
            out.append(line)
        data_file = "output" + str(agent_uid) + ".csv"
        if os.path.exists(data_file): os.remove(data_file)
        f = open(data_file,"x")
        for line in out:
            f.writelines(line + "\n")
        f.close()
        
    def plot_extracted_data(self, model):
        extr_data = model.extracted_car_data
        time_steps = [time_step for time_step in extr_data.keys()]
        data_elements_per_agent \
            = list(next(iter(next(iter(extr_data.values())).values())).keys())
        lbl_time_steps, lbl_hour_steps = time_axis_labels(time_steps)
        
        for element in data_elements_per_agent:
            fig, ax = plt.subplots()
            for agent in next(iter(extr_data.values())):
                soc = [time_step[agent][element] \
                       for time_step in extr_data.values()]
                plt.xticks(lbl_time_steps, lbl_hour_steps)
                plt.grid(axis='x', color='0.95')
                ax.plot(time_steps, soc)
            ax.set(xlabel='time in hours', ylabel=element)
            plt.show()
            
    def print_overall_charging_results(self, model):
        charge_sets = ["charge_received_work", "charge_received_pv",
                       "charge_received_grid", "charge_received_public"]
        time_steps = [time_step for time_step in model.extracted_car_data.keys()]
        charges = dict()
        for charge_set in charge_sets:
            charges[charge_set] = []
            for time_step, time_step_data in model.extracted_car_data.items():
                charge = 0
                for agent in time_step_data.values():
                    charge += agent[charge_set]
                charges[charge_set].append(charge)
            print("{}: {:.01f} kWh".format(charge_set,
                                           sum(charges[charge_set])))
        
        average_company_charger_utilisation \
            = [sum(time_step_data) / len(time_step_data) for time_step_data \
               in model.extracted_company_data["Charger utilisation"]]
                
        print("Company Charger Utilisation: {:.02f}%".format( \
            sum(average_company_charger_utilisation) * 100 \
            / len(average_company_charger_utilisation)))
        
    def plot_parameter_scan(self, scan_parameters, scan_collected_data):
        if len(scan_parameters) == 1:
            fig, ax = plt.subplots()
            for name, data_set in scan_collected_data.items():
                ax.plot(list(scan_parameters.values())[0], data_set,
                        label=name)
            ax.set(xlabel=list(scan_parameters.keys())[0])
            plt.legend()
            plt.show()
            for name, data_set in scan_collected_data.items():
                fig, ax = plt.subplots()
                time_steps = list(scan_parameters.values())[0]
                ax.plot(time_steps, data_set)
                ax.set(xlabel=list(scan_parameters.keys())[0], ylabel=name)
                plt.xticks(time_axis_labels(time_steps))
                plt.show()
                
    def evaluate_overall_charge(self, model):
        charge_sets = ["charge_received_work", "charge_received_pv",
                       "charge_received_grid", "charge_received_public"]
        time_steps = [time_step for time_step in model.extracted_car_data.keys()]
        charges = dict()
        for charge_set in charge_sets:
            charges[charge_set] = []
            for time_step, time_step_data in model.extracted_car_data.items():
                charge = 0
                for agent in time_step_data.values():
                    charge += agent[charge_set]
                charges[charge_set].append(charge)
        
        fig, ax = plt.subplots()
        for name, charge in charges.items():
            ax.plot(time_steps, charge, label=name)
        ax.set(xlabel="time in minutes")
        plt.legend()
        plt.show()
        
        # show all individual company utilisation
        fig, ax = plt.subplots()
        ax.plot(time_steps, model.extracted_company_data["Charger utilisation"])
        ax.set(xlabel="time in minutes", ylabel="Charger utilisation")
        plt.show()
        
        fig, ax = plt.subplots()
        average_company_charger_utilisation \
            = [sum(time_step_data) / len(time_step_data) for time_step_data \
               in model.extracted_company_data["Charger utilisation"]]
        ax.plot(time_steps, average_company_charger_utilisation)
        ax.set(xlabel="time in minutes", ylabel="Average charger utilisation")
        plt.show()
        
    def print_route_stats(self, model):
        route_lengths = []
        for agent in model.schedule_cars.agents:
            home = agent.house_agent.location
            work = agent.company.location
            route = model.lrm.calc_route(home, work)
            length = None
            if len(route) >= 2:
                length = model.lrm.calc_route_length(route)
            else:
                length = agent.distance_commuted_if_work_and_home_equal
            route_lengths.append(length)
        print("Route (min / avg / max) = {:.1f} km / {:.1f} km / {:.1f} km".format(\
            min(route_lengths), sum(route_lengths)/len(route_lengths),
            max(route_lengths)))