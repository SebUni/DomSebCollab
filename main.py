# -*- coding: utf-8 -*-
"""
Created on Sun Jan 17 17:32:43 2021

@author: S3739258
"""

import charging_model
import matplotlib.pyplot as plt

from parameters import Parameters

def time_stamp(i):
    parameters = Parameters()
    time_step = parameters.get_parameter("time_step","int")
    hours = i * time_step // 60
    minutes = i * time_step - hours * 60
    
    return format(hours,"02") + ":" + format(minutes,"02")

def draw_car_agents(model, it):
    x_vals = []
    y_vals = []
    for boid in model.schedule_cars.agents:
        x, y = boid.pos
        x_vals.append(x)
        y_vals.append(y)
    fig = plt.figure(figsize=(10,10))
    ax = fig.add_subplot(111)
    ax.scatter(x_vals, y_vals)
    ax.text(0, 0, time_stamp(it), fontsize=24)
    ax.axis('off')
    title = str(it) + ".png"
    fig.savefig(title)

draw_soc_chart = False
draw_agents_on_map = True

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
            for j, it in enumerate(cm.extracted_soc):
                y = it
                y = y[-(i-130):]
                plt.plot(x, y, label = "line " + str(j) )
            plt.show()
    if draw_agents_on_map:
        draw_car_agents(cm, i)
cm.summarise_simulation()