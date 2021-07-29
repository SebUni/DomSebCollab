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
    if i == 2016:
        test = 0
    cm.step()
    if draw_agents_on_map:
        od.draw_car_agents(cm, i)
cm.summarise_simulation()

od.print_route_stats(cm)
od.print_overall_charging_results(cm)

if plot_extraced_data:
    od.plot_extracted_data(cm)
    od.evaluate_overall_charge(cm)


# parameter scan
# scan_parameters = {"prices_at_work" : np.arange (0.2, 0.21, 0.001)}
# scan_collected_data = {"charge_home" :[], "charge_work" : [],
#                        "charge_emergency" : [], "utilisation" : []}
# for price_at_work in scan_parameters["prices_at_work"]:
#     print(price_at_work)
#     parameters.parameters["company_charger_cost_per_kWh"] = price_at_work
#     cm = charging_model.ChargingModel(nbr_of_agents, parameters)
#     for i in range(cm.clock.time_step_limit):
#         cm.step()
#     cm.summarise_simulation()
#     od.print_overall_charging_results(cm)
    
#     total_charge = cm.total_charge()
#     scan_collected_data["charge_home"].append(total_charge["home"])
#     scan_collected_data["charge_work"].append(total_charge["work"])
#     scan_collected_data["charge_emergency"].append(total_charge["emergency"])
#     scan_collected_data["utilisation"].append(\
#                                 cm.lrm.average_company_charger_utilisation())

# od.plot_parameter_scan(scan_parameters, scan_collected_data)