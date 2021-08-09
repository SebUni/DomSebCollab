#
"""
Created on Sun Jan 17 17:32:43 2021

@author: S3739258
"""

import numpy as np

import charging_model
from parameters import Parameters
from output_data import OutputData
from console_output import ConsoleOutput

draw_agents_on_map = False
plot_extraced_data = True
plot_extraced_data_details = True

run_parameter_scan = False

co = ConsoleOutput()
parameters = Parameters()
od = OutputData(co, parameters)
nbr_of_agents = parameters.get("nbr_of_agents","int")

# single run
if not run_parameter_scan:
    cm = charging_model.ChargingModel(nbr_of_agents, co, parameters)
    for i in range(cm.clock.time_step_limit):
        if i == 2016:
            test = 0
        cm.step()
        if draw_agents_on_map:
            od.draw_car_agents(cm, i)
    cm.summarise_simulation()
    
    od.print_route_stats(cm)
    od.print_house_stats(cm)
    od.print_overall_charging_results(cm)
    
    if plot_extraced_data:
        od.evaluate_overall_charge(cm)
    if plot_extraced_data_details:
        od.plot_extracted_data(cm)


# parameter scan
else:
    scan_parameters = {"prices_at_work" : np.arange (0.14, 0.29, 0.02),
                        "employees_per_charger" : range(1,2,9)}
    for employees_per_charger in scan_parameters["employees_per_charger"]:
        scan_collected_data = {"charge_pv" :[], "charge_work" : [],
                               "charge_grid" :[], "charge_emergency" : [],
                               "utilisation" : [], "avg_cost_apartment": [],
                               "avg_cost_house_pv": [],
                               "avg_cost_house_no_pv": [], "avg_cost": []}
        for price_at_work in scan_parameters["prices_at_work"]:
            parameters.parameters["company_charger_cost_per_kWh"] \
                = price_at_work
            parameters.parameters["employees_per_charger"] \
                = employees_per_charger 
            cm = charging_model.ChargingModel(nbr_of_agents, parameters)
            for i in range(cm.clock.time_step_limit):
                cm.step()
            cm.summarise_simulation()    
            od.print_route_stats(cm)
            od.print_overall_charging_results(cm)
                
            charge_pv, charge_work, charge_grid, charge_emergency, \
            utilisation, avg_cost_apartment, avg_cost_house_pv, \
            avg_cost_house_no_pv, avg_cost \
                = od.calc_overall_charging_results(cm)
                
            scan_collected_data["charge_pv"].append(charge_pv)
            scan_collected_data["charge_work"].append(charge_work)
            scan_collected_data["charge_grid"].append(charge_grid)
            scan_collected_data["charge_emergency"].append(charge_emergency)
            scan_collected_data["utilisation"].append(utilisation)
            scan_collected_data["avg_cost_apartment"].append(avg_cost_apartment)
            scan_collected_data["avg_cost_house_pv"].append(avg_cost_house_pv)
            scan_collected_data["avg_cost_house_no_pv"].append(avg_cost_house_no_pv)
            scan_collected_data["avg_cost"].append(avg_cost)
        
        title = "employees_per_charger_{}".format(employees_per_charger)
        slct_scan_parameters = dict()
        slct_scan_parameters["prices_at_work"] \
            = scan_parameters["prices_at_work"]
        od.plot_parameter_scan(slct_scan_parameters, scan_collected_data,
                               title)
        
co.clean_logger()