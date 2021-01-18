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

cm = charging_model.ChargingModel(100,2)
for i in range(6*24*5):
    cm.step()
    draw_car_agents(cm, i)


