#
"""
Created on Sun Jan 17 17:32:43 2021

@author: S3739258
"""

import numpy as np

import charging_model
from parameters import Parameters
from output_data import OutputData

draw_agents_on_map = False
plot_extraced_data = True

parameters = Parameters()
od = OutputData(parameters)
nbr_of_agents = parameters.get_parameter("nbr_of_agents","int")

# single run
cm = charging_model.ChargingModel(nbr_of_agents, parameters)
for i in range(cm.clock.time_step_limit):
    if i in [2200, 2400, 2600, 2800, 3000, 3200, 3400]:
        test = 0;
    cm.step()
    if draw_agents_on_map:
        od.draw_car_agents(cm, i)
cm.summarise_simulation()

od.print_overall_charging_results(cm)

if plot_extraced_data:
    od.plot_extracted_data(cm)


# parameter scan
# for price_at_work in np.arange (0.5, 0.45, 0.5):
#     parameters.parameters["company_charger_cost_per_kWh"] = price_at_work
#     cm = charging_model.ChargingModel(nbr_of_agents, parameters)
#     for i in range(cm.clock.time_step_limit):
#         cm.step()
#         if draw_agents_on_map:
#             od.draw_car_agents(cm, i)
#     cm.summarise_simulation()
#     od.print_overall_charging_results(cm)
#     if plot_extraced_data:
#         od.plot_extracted_data(cm)
