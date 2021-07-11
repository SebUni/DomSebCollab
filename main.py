# -*- coding: utf-8 -*-
"""
Created on Sun Jan 17 17:32:43 2021

@author: S3739258
"""

import os
import matplotlib.pyplot as plt

import charging_model
from parameters import Parameters

def time_stamp(i):
    parameters = Parameters()
    time_step = parameters.get_parameter("time_step","int")
    days = i * time_step // 60 // 24
    day_of_week = int(days % 7)
    hours = i * time_step // 60
    hour_of_day = int(hours % 24)
    minutes = int(i * time_step - hours * 60)
    
    
    return "{:d}d {:02d}h {:02d}m".format(round(day_of_week+1),
                                         round(hour_of_day),
                                         round(minutes))

def draw_car_agents(model, it):
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
    ax.text(0, 0, time_stamp(it), fontsize=24)
    ax.axis('off')
    title = "{:06d}".format(it) + ".png"
    fig.savefig(title, bbox_inches='tight', pad_inches=0)
    
    # pngs to gif using cmd "magick convert -delay 1 -loop 0 *.png animation.gif"
    # do not connect more than a day
    # overlay gif with map using cmd "magick convert output.gif -layers optimize result.gif"
    # concatenate mutiple using cmd "magick convert day*_map_opt.gif week.gif"

draw_soc_chart = False
draw_agents_on_map = False

parameters = Parameters()
nbr_of_agents = parameters.get_parameter("nbr_of_agents","int")

cm = charging_model.ChargingModel(nbr_of_agents)

for i in range(cm.clock.time_step_limit):
    if i == 21:
        test = 1
    cm.step()
    if draw_soc_chart:
        if 130 < i < 170:
            x = list(range(i+1))
            x = x[-(i-130):]
            for j, it in enumerate(cm.extracted_data):
                y = it
                y = y[-(i-130):]
                plt.plot(x, y, label = "line " + str(j) )
            plt.show()
    if draw_agents_on_map:
        draw_car_agents(cm, i)
cm.summarise_simulation()

# data_file = "output_car_data.csv"
# data_elements_per_agent \
#     = list(next(iter(next(iter(cm.extracted_data.values())).values())).keys())

# if os.path.exists(data_file): os.remove(data_file)
# f = open(data_file,"x")
    
# data_header = "Elapsed time"
# for i in range(cm.num_agents):
#     for element in data_elements_per_agent:
#         data_header += "," + str(element)
# f.writelines(data_header + "\n")

# for time_step, time_step_data in cm.extracted_data.items():
#     line = str(time_step)
#     for agent_data in time_step_data.values():
#         for element in data_elements_per_agent:
#             line += "," + str(agent_data[element])
#     f.writelines(line + "\n")
# f.close()

time_steps = [time_step for time_step in cm.extracted_data.keys()]
for agent in next(iter(cm.extracted_data.values())):
    soc = [time_step[agent]["soc"] for time_step in cm.extracted_data.values()]
    plt.plot(time_steps, soc)
plt.show()
for agent in next(iter(cm.extracted_data.values())):
    emergency_instruction \
        = [time_step[agent]["emergency_charge_instruction"] for time_step in cm.extracted_data.values()]
    plt.plot(time_steps, emergency_instruction)
plt.show()
for agent in next(iter(cm.extracted_data.values())):
    home_instruction \
        = [time_step[agent]["home_charge_instruction"] for time_step in cm.extracted_data.values()]
    plt.plot(time_steps, home_instruction)
plt.show()
for agent in next(iter(cm.extracted_data.values())):
    work_instruction \
        = [time_step[agent]["work_charge_instruction"] for time_step in cm.extracted_data.values()]
    plt.plot(time_steps, work_instruction)
plt.show()

# output one agent to file
# elems = list(data[2023].keys())
# out = []
# out.append("time_step," + ",".join(elems))
# for time_step, data in cm.extracted_data.items():
#     line = str(time_step)
#     for elem in elems:
#         if isinstance(data[2023][elem], int):
#             line += ",{}".format(data[2023][elem])
#         else:
#             line += ",{:.03f}".format(data[2023][elem])
#     out.append(line)
# data_file = "output.csv"
# if os.path.exists(data_file): os.remove(data_file)
# f = open(data_file,"x")
# for line in out:
#     f.writelines(line + "\n")
# f.close()

total_charge = {"home":0, "work":0, "emergency":0}
for agent in cm.schedule_cars.agents:
    total_charge["home"] += agent.total_charge["home"]
    total_charge["work"] += agent.total_charge["work"]
    total_charge["emergency"] += agent.total_charge["emergency"]
print("Charge: @home = {}, @work = {}, @emergency = {},".format(total_charge["home"],
                                                                total_charge["work"],
                                                                total_charge["emergency"]))
print("Company Charger Utilisation: {}".format(cm.lrm.average_company_charger_utilisation()))