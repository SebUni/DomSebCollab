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
import average_seasons
import gc

draw_agents_on_map = False
plot_extraced_data = False
plot_extraced_data_details = False
store_to_csv = True

sweep_season = True
sweep_parameters = True
    
def exec_single_run(parameters, co, od):
    nbr_of_agents = parameters.get("nbr_of_agents","int")
    cm = charging_model.ChargingModel(nbr_of_agents, co, parameters)
    for i in range(cm.clock.time_step_limit):
        if i == 2016:
            test = 0
        cm.step()
        if draw_agents_on_map and i>=parameters.get("pre_heat_steps", "int"):
            od.draw_car_agents(cm, i)
    cm.summarise_simulation()
    
    od.print_route_stats(cm)
    od.print_house_stats(cm)
    od.print_overall_charging_results(cm)
    
    if plot_extraced_data:
        od.evaluate_overall_charge(cm)
    if plot_extraced_data_details:
        od.plot_extracted_data(cm)
    if store_to_csv:
        od.store_time_series_to_csv(cm)
    cm.clear()
    del cm
    gc.collect()

def exec_parameter_sweep(parameters, co, od):
    nbr_of_agents = parameters.get("nbr_of_agents","int")
    scan_parameters = {"employees_per_charger" : range(55,62,6),
                "company_charger_cost_per_kWh" : np.arange (0.04, 0.33, 0.01)}
    scan_order = ["employees_per_charger","company_charger_cost_per_kWh"]
    scan_collected_data = {"charge_pv":[], "charge_work": [], "charge_grid":[],
                           "charge_emergency": [], "charge_held_back": [],
                           "utilisation": [], "total_revenue": [],
                           "revenue_per_charger": [],"avg_cost_apartment": [],
                           "avg_cost_house_pv": [], "avg_cost_house_no_pv": [],
                           "avg_cost": []}
    if len(scan_parameters[scan_order[0]]) == 0:
        scan_parameters[scan_order[0]] = [parameters.get(scan_order[0],"float")]
    for outer_parameter in scan_parameters[scan_order[0]]:
        parameters.parameters[scan_order[0]] = outer_parameter
        for inner_parameter in scan_parameters[scan_order[1]]:
            parameters.parameters[scan_order[1]] = inner_parameter 
            cm = charging_model.ChargingModel(nbr_of_agents, co, parameters)
            for i in range(cm.clock.time_step_limit):
                cm.step()
            cm.summarise_simulation()    
            od.print_route_stats(cm)
            od.print_house_stats(cm)
            od.print_overall_charging_results(cm)
                
            charge_pv, charge_work, charge_grid, charge_emergency, \
            charge_held_back, utilisation, total_revenue, revenue_per_charger,\
            avg_cost_apartment, avg_cost_house_pv, avg_cost_house_no_pv, \
            avg_cost = od.calc_overall_charging_results(cm)
                
            scan_collected_data["charge_pv"].append(charge_pv)
            scan_collected_data["charge_work"].append(charge_work)
            scan_collected_data["charge_grid"].append(charge_grid)
            scan_collected_data["charge_emergency"].append(charge_emergency)
            scan_collected_data["charge_held_back"].append(charge_held_back)
            scan_collected_data["utilisation"].append(utilisation)
            scan_collected_data["total_revenue"].append(total_revenue)
            scan_collected_data["revenue_per_charger"].append(revenue_per_charger)
            scan_collected_data["avg_cost_apartment"].append(avg_cost_apartment)
            scan_collected_data["avg_cost_house_pv"].append(avg_cost_house_pv)
            scan_collected_data["avg_cost_house_no_pv"].append(avg_cost_house_no_pv)
            scan_collected_data["avg_cost"].append(avg_cost)
            cm.clear()
            del cm
            gc.collect()
    
    if store_to_csv:
        od.store_sweep_parameters_to_csv(scan_parameters, scan_order,
                                         scan_collected_data)
    if plot_extraced_data:
        od.plot_sweep_parameters(scan_parameters, scan_order,
                                 scan_collected_data) 

# prepare parameters
parameters = Parameters()
seasons = list(range(4)) if sweep_season else [parameters.get("season","int")]
for season in seasons:
    parameters.setter("season", season)
    co = ConsoleOutput(parameters.path_file_name("log", ".log"))
    od = OutputData(co, parameters)
    # conduct simulation
    if not sweep_parameters:
        exec_single_run(parameters, co, od)
    else:
        exec_parameter_sweep(parameters, co, od)
    # clean up logger
    co.clean_logger()
# if season sweep average results
if sweep_season:
    model = parameters.get("charging_model","int")
    nbr_of_agents = parameters.get("nbr_of_agents","int")
    average_seasons.exec_avg(model, nbr_of_agents, plot_extraced_data)
