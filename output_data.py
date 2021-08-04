# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 15:01:29 2021

@author: S3739258
"""

import os
import fiona
import matplotlib.pyplot as plt
import matplotlib.patches

from console_output import ConsoleOutput

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

def get_color(value, min_value, max_value):
    _max = max(abs(min_value), max_value)
    rel_value = value / _max
    if rel_value <= 0:
        return [1+rel_value,1+rel_value,1]
    else:
        return [1,1-rel_value,1-rel_value]    

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
    
    def calc_overall_charging_results(self, model):
        charge_pv, charge_work, charge_grid, charge_emergency = 0, 0, 0, 0
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
            if charge_set == "charge_received_work":
                charge_work = sum(charges[charge_set])
            if charge_set == "charge_received_pv":
                charge_pv = sum(charges[charge_set])
            if charge_set == "charge_received_grid":
                charge_grid = sum(charges[charge_set])
            if charge_set == "charge_received_public":
                charge_emergency = sum(charges[charge_set])
        
        charger_utilisations \
            = [list(time_step.values()) for time_step in \
               model.extracted_company_data["Charger utilisation"]]
        average_company_charger_utilisation \
            = [sum(time_step_data) / len(time_step_data) for time_step_data \
               in charger_utilisations]
        utilisation = sum(average_company_charger_utilisation) * 100 \
            / len(average_company_charger_utilisation)

        total_electricity_cost_apartment \
            = sum([sum([agent["electricity_cost_apartment"] \
                    for agent in time_step_data.values()]) \
                for time_step_data in model.extracted_car_data.values()])
        total_electricity_cost_w_pv \
            = sum([sum([agent["electricity_cost_house_w_pv"] \
                    for agent in time_step_data.values()]) \
                for time_step_data in model.extracted_car_data.values()])
        total_electricity_cost_wo_pv \
            = sum([sum([agent["electricity_cost_house_wo_pv"] \
                    for agent in time_step_data.values()]) \
                for time_step_data in model.extracted_car_data.values()])
        total_electricity_cost = total_electricity_cost_apartment + \
            total_electricity_cost_w_pv + total_electricity_cost_wo_pv
            
        total_dist_travlled_apartment \
            = sum([sum([agent["distance_travelled_apartment"] \
                    for agent in time_step_data.values()]) \
                for time_step_data in model.extracted_car_data.values()])
        total_dist_travlled_w_pv \
            = sum([sum([agent["distance_travelled_house_w_pv"] \
                    for agent in time_step_data.values()]) \
                for time_step_data in model.extracted_car_data.values()])
        total_dist_travlled_wo_pv \
            = sum([sum([agent["distance_travelled_house_wo_pv"] \
                    for agent in time_step_data.values()]) \
                for time_step_data in model.extracted_car_data.values()])
        total_dist_travlled = total_dist_travlled_apartment \
            + total_dist_travlled_w_pv + total_dist_travlled_wo_pv
            
        nbr_agent_apartments = sum([0 if agent.house_agent.is_house else 1 \
                                   for agent in model.schedule_cars.agents])
        nbr_agents_w_pv = sum([1 if agent.house_agent.pv_capacity != 0 else 0 \
                                   for agent in model.schedule_cars.agents])
        nbr_agents_wo_pv = len(model.schedule_cars.agents) \
            - nbr_agent_apartments - nbr_agents_w_pv
        total_nbr_agents \
            = nbr_agent_apartments + nbr_agents_w_pv + nbr_agents_wo_pv
        
        
        avg_electricity_cost_apartment, avg_electricity_cost_w_pv, \
            avg_electricity_cost_wo_pv, avg_dist_travlled_apartment, \
            avg_dist_travlled_w_pv, avg_dist_travlled_wo_pv = 0, 0, 0, 0, 0, 0
        avg_electricity_cost, avg_dist_travlled = 0, 0
        if nbr_agent_apartments != 0:
            avg_electricity_cost_apartment  \
                = total_electricity_cost_apartment/  nbr_agent_apartments
            avg_dist_travlled_apartment \
                = total_dist_travlled_apartment / nbr_agent_apartments
        if nbr_agents_w_pv != 0:
            avg_electricity_cost_w_pv \
                = total_electricity_cost_w_pv / nbr_agents_w_pv
            avg_dist_travlled_w_pv \
                = total_dist_travlled_w_pv / nbr_agents_w_pv
        if nbr_agents_wo_pv != 0:
            avg_electricity_cost_wo_pv \
                = total_electricity_cost_wo_pv / nbr_agents_wo_pv
            avg_dist_travlled_wo_pv \
                = total_dist_travlled_wo_pv / nbr_agents_wo_pv
        if total_nbr_agents != 0:
            avg_electricity_cost = total_electricity_cost / total_nbr_agents
            avg_dist_travlled = total_dist_travlled / total_nbr_agents
        
        avg_cost_apartment_per_km = 0
        if avg_dist_travlled_apartment != 0:
            avg_cost_apartment_per_km \
                = avg_electricity_cost_apartment / avg_dist_travlled_apartment
        avg_cost_house_pv_per_km = 0
        if avg_dist_travlled_w_pv != 0:
            avg_cost_house_pv_per_km \
                = avg_electricity_cost_w_pv / avg_dist_travlled_w_pv
        avg_cost_house_no_pv_per_km = 0
        if avg_dist_travlled_wo_pv != 0:
            avg_cost_house_no_pv_per_km \
                = avg_electricity_cost_wo_pv / avg_dist_travlled_wo_pv
        avg_cost_per_km = 0
        if avg_dist_travlled != 0:
            avg_cost_per_km = avg_electricity_cost / avg_dist_travlled
        
        return charge_pv, charge_work, charge_grid, charge_emergency, \
            utilisation, avg_cost_apartment_per_km, avg_cost_house_pv_per_km, \
            avg_cost_house_no_pv_per_km, avg_cost_per_km
        
    def print_overall_charging_results(self, model):
        co = ConsoleOutput()
        co.t_print("COMMENCING DATA EVALUATION")    
        charge_pv, charge_work, charge_grid, charge_emergency, utilisation, \
        avg_cost_apartment, avg_cost_house_pv, avg_cost_house_no_pv, avg_cost \
            = self.calc_overall_charging_results(model)
        co.t_print("charge_received_work: {:.01f} kWh".format(charge_work))
        co.t_print("charge_received_pv: {:.01f} kWh".format(charge_pv))
        co.t_print("charge_received_grid: {:.01f} kWh".format(charge_grid))
        co.t_print("charge_received_public: {:.01f} kWh".format(\
                                                        charge_emergency))
        co.t_print("Company Charger Utilisation: {:.02f}%".format(utilisation))
        co.t_print("Average Electricity Cost for Apartments: ${:.04f}".format(\
                                                        avg_cost_apartment))
        co.t_print("Average Electricity Cost for House wo PV: ${:.04f}".format(\
                                                        avg_cost_house_no_pv))
        co.t_print("Average Electricity Cost for House w PV: ${:.04f}".format(\
                                                        avg_cost_house_pv))
        co.t_print("Average Electricity Cost: ${:.04f}".format(avg_cost))
        co.t_print("DATA EVALUATION COMPLETE")
        
    def print_route_stats(self, model):
        co = ConsoleOutput()
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
        co.t_print("Route (min / avg / max) = {:.1f} km / {:.1f} km / {:.1f} km".format(\
            min(route_lengths), sum(route_lengths)/len(route_lengths),
            max(route_lengths)))
        co.t_print("Average Consumption {:.1f} kWh".format(\
            sum([sum([agent["charge_consumed"] \
                  for agent in time_step_data.values()])\
                 for time_step_data in model.extracted_car_data.values()]) \
                / len(model.schedule_cars.agents)))
        
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
                ax.plot(time_steps, soc)
            ax.set(xlabel='time in hours', ylabel=element)
            plt.xticks(lbl_time_steps, lbl_hour_steps)
            plt.grid(axis='x', color='0.95')
            plt.show()
        
    def plot_parameter_scan(self, scan_parameters, scan_collected_data, title):
        if len(scan_parameters) == 1:
            # fig, ax = plt.subplots()
            # for name, data_set in scan_collected_data.items():
            #     ax.plot(list(scan_parameters.values())[0], data_set,
            #             label=name)
            # ax.set(xlabel=list(scan_parameters.keys())[0])
            # plt.legend()
            # plt.show()
            # for name, data_set in scan_collected_data.items():
            #     fig, ax = plt.subplots()
            #     time_steps = list(scan_parameters.values())[0]
            #     ax.plot(time_steps, data_set)
            #     ax.set(xlabel=list(scan_parameters.keys())[0], ylabel=name)
            #     plt.show()
            # general data
            time_steps = list(scan_parameters.values())[0]
            directory = "results/"
            # plot consumption
            fig, ax = plt.subplots()
            ax.plot(time_steps, scan_collected_data["charge_pv"],
                    label="charge_pv")
            ax.plot(time_steps, scan_collected_data["charge_work"], 
                    label="charge_work")
            ax.plot(time_steps, scan_collected_data["charge_grid"],
                    label="charge_grid")
            ax.plot(time_steps, scan_collected_data["charge_emergency"],
                    label="charge_emergency")
            ax.set(xlabel=list(scan_parameters.keys())[0], ylabel="kWh")
            plt.title(title)
            plt.legend()
            plt.show()
            file_name = directory + title + "_consumption.png"
            fig.savefig(file_name, bbox_inches='tight', pad_inches=0)
            # plot utilisation
            fig, ax = plt.subplots()
            ax.plot(time_steps, scan_collected_data["utilisation"],
                    label="utilisation")
            ax.set(xlabel=list(scan_parameters.keys())[0], ylabel="utilisation in %")
            plt.title(title)
            plt.show()
            file_name = directory + title + "_utilisation.png"
            fig.savefig(file_name, bbox_inches='tight', pad_inches=0)
            # plot cost
            fig, ax = plt.subplots()
            ax.plot(time_steps, scan_collected_data["avg_cost_apartment"],
                    label="avg_cost_apartment")
            ax.plot(time_steps, scan_collected_data["avg_cost_house_pv"], 
                    label="avg_cost_house_pv")
            ax.plot(time_steps, scan_collected_data["avg_cost_house_no_pv"],
                    label="avg_cost_house_no_pv")
            ax.plot(time_steps, scan_collected_data["avg_cost"],
                    label="avg_cost")
            ax.set(xlabel=list(scan_parameters.keys())[0], ylabel="$/km")
            plt.legend()
            plt.title(title)
            plt.show()
            file_name = directory + title + "_cost.png"
            fig.savefig(file_name, bbox_inches='tight', pad_inches=0)
            
                
    def evaluate_overall_charge(self, model):
        charge_sets = ["charge_received_work", "charge_received_pv",
                       "charge_received_grid", "charge_received_public"]
        time_steps = [time_step for time_step in model.extracted_car_data.keys()]
        lbl_time_steps, lbl_hour_steps = time_axis_labels(time_steps)
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
        plt.xticks(lbl_time_steps, lbl_hour_steps)
        plt.grid(axis='x', color='0.95')
        plt.legend()
        plt.show()
        
        # show all individual company utilisation
        charger_utilisations \
            = [list(time_step.values()) for time_step in \
               model.extracted_company_data["Charger utilisation"]]
        fig, ax = plt.subplots()
        ax.plot(time_steps, charger_utilisations)
        ax.set(xlabel="time in minutes", ylabel="Charger utilisation")
        plt.xticks(lbl_time_steps, lbl_hour_steps)
        plt.grid(axis='x', color='0.95')
        plt.show()
        
        fig, ax = plt.subplots()
        average_company_charger_utilisation \
            = [sum(time_step) / len(time_step) for time_step \
               in charger_utilisations]
        ax.plot(time_steps, average_company_charger_utilisation)
        ax.set(xlabel="time in minutes", ylabel="Average charger utilisation")
        plt.xticks(lbl_time_steps, lbl_hour_steps)
        plt.grid(axis='x', color='0.95')
        plt.show()
        
    def evaluate_geographic_charge_distribution(self, model):
        # parameters to retrieve area border gps data
        SA4_regions_to_include = [206,207,208,209,210,211,212,213,214]
        export_SA_level = model.parameters.get_parameter("sa_level","int")
        _layer = "Statistical_Area_Level_" + str(export_SA_level) + "_2016"
        _code = None
        _name = "SA" + str(export_SA_level) + "_NAME_2016"
        if 3 <= export_SA_level <= 4:
            _code = "SA" + str(export_SA_level) + "_CODE_2016"
        elif export_SA_level == 2:
            _code = "SA" + str(export_SA_level) + "_MAINCODE_2016"
        elif export_SA_level == 1:
            raise RuntimeError("SA code not implemented!")
        else:
            raise RuntimeError("Ill defined SA code!")
        # extract data from model
        min_charge_delivered = 0
        max_charge_delivered = 0
        for location in model.lrm.locations.values():
            charge_delivered = location.total_charge_delivered
            min_charge_delivered = min(min_charge_delivered, charge_delivered)
            max_charge_delivered = max(max_charge_delivered, charge_delivered)
        
        # Check if retreived data fits map data
        # data retrieved from
        # https://data.gov.au/data/dataset/asgs-2016-edition-boundaries
        _file_name = "asgs2016absstructuresmainstructureandgccsa.gpkg"
        _file_path \
            = "data\\generators\\locations\\sa_code, sa_names, cooridnates\\"
        # export_level_region_names = dict()
        # with fiona.open(_file_path + _file_name, layer=_layer) as layer:
        #     for export_level_region in layer:
        #         elr = export_level_region
        #         is_in_selected_SA4_region = False
        #         for SA4_region in SA4_regions_to_include:
        #             if str(SA4_region) \
        #                 == elr['properties'][_code][:len(str(SA4_region))]:
        #                 is_in_selected_SA4_region = True
        #                 break
        #         if is_in_selected_SA4_region:
        #             elr_code = elr['properties'][_code]
        #             export_level_region_names[elr_code] \
        #                 = elr['properties'][_name]
        
        # if len(export_level_region_names) != len(charge_values):
        #     raise RuntimeError("draw_consumption.py: # of pbc values "\
        #                        + "doesn't match # of Stat. Areas!")
        
        # plot data
        fig = plt.figure(figsize=(13,13))
        ax = fig.add_subplot(111)
        with fiona.open(_file_path + _file_name, layer=_layer) as layer:
            nbr_of_drawn_sas = 0
            for export_level_region in layer:
                elr = export_level_region
                is_in_selected_SA4_region = False
                for SA4_region in SA4_regions_to_include:
                    if str(SA4_region) \
                        == elr['properties'][_code][:len(str(SA4_region))]:
                        is_in_selected_SA4_region = True
                        break
                if is_in_selected_SA4_region:
                    elr_code = int(elr['properties'][_code])
                    charge_value \
                        = model.lrm.locations[elr_code].total_charge_delivered
                    color_data = get_color(charge_value, min_charge_delivered,
                                           max_charge_delivered)
                    for patch_data in elr['geometry']['coordinates']:
                        x = [data[0] for data in patch_data[0]]
                        y = [data[1] for data in patch_data[0]]
                        p = matplotlib.patches.Polygon(patch_data[0],
                                                       facecolor=color_data)
                        ax.add_patch(p)
                        ax.plot(x, y, color='black', linewidth=1)    
                    nbr_of_drawn_sas += 1
        
        ax.margins(0.1)
        ax.axis('off')
        plt.show()