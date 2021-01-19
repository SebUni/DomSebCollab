# -*- coding: utf-8 -*-
"""
Created on Sun Jan 17 17:32:43 2021

@author: S3739258
"""

import charging_model
import matplotlib.pyplot as plt

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
    title = str(it) + ".png"
    fig.savefig(title)

cm = charging_model.ChargingModel(50,4)
for i in range(6*24*5):
    cm.step()
    if 130 < i < 170:
        x = list(range(i+1))
        x = x[-(i-130):]
        for j, it in enumerate(cm.extracted_soc):
            y = it
            y = y[-(i-130):]
            plt.plot(x, y, label = "line " + str(j) )
        plt.show()

    # draw_car_agents(cm, i)
