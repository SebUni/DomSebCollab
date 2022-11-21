# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 13:06:27 2020

@author: S3739258
"""
import math

from mesa import Agent

from charging_strategy import ChargingStrategy
from cal import Cal


class CarAgent(Agent):
    """An agent which can travel along the map."""
    def __init__(self, uid, model, tracking_id, clock, cur_activity,
                 cur_location, house_agent, company, location_road_manager,
                 car_model_manager, whereabouts_manager, calendar_planer,
                 extracted_data, parameters):
        """
        Parameters
        ----------
        uid : int
            Unique of the car agent.
        model : ChargingModel
            The base charging model defined as base for the simulation.
        clock : Clock
            The Handle to the global clock object.
        house_agent : HouseAgent
            The house_agent assigned to this car_agent.
        company : Company
            The company where this agent is working.
        location_road_manager : LocationRoadManager
            Handle to the location road manager.
        car_model_manager : CarModelManager
            The object handling all car models created in ChargingModel class.
        whereabouts_manager : WhereaboutsManager
            The object handling all whereabouts created in ChargingModel class.
        calendar_planer: CalendarPlaner
            The object handling the creation of calendars across the
            simulation.
        parameters: Parameters
            Provides external parameters.
            
        Parameters handed by Parameter class
        ----------
        departure_condition : string
            Ensures that car never runs out of power midway. Can take three
            different values:
                ROUND_TRIP   = SOC needs to allow for completing next route
                               twice (back and forth) PLUS reserve_range.
                ONE_WAY_TRIP = SOC needs to allow for completing next route
                               once PLUS reserve_range.
                NEXT_NODE    = SOC needs to allow for reaching the next node
                               PLUS reserve_range.
        reserve_range : int
            Range the car needs to be able drive without charging in km.
        reserve_speed : int
            Velocity assumed car is driving maximum once it hits reserve in
            km/h.
        queuing_condition : string
            Allows to choose if the car owner is actively trying to charge its
            car in case all chargers are blocked by the time of arrival. That
            is, return later once a charger is available or just leave the car
            not charging in case there is no charger available by the time of
            arrival. Can take two values:
                ALWAYS      = Que everytime a destination is reached.
                WHEN_NEEDED = Only if the departure criteria is not satisfied.

        Returns
        -------
        None.
        """
        super().__init__(uid, model)
        # uid is redundant because super alreay incorperates unique_id but
        # for brevity and consistency through out the code i define uid
        self.uid = uid 
        self.tracking_id = tracking_id
        self.parameters = parameters
        self.clock = clock
        self.house_agent = house_agent
        self.company = company
        self.distance_commuted_if_work_and_home_equal \
            = house_agent.location.draw_distance_commuted_if_work_equal_home_at_random()
        self.lrm = location_road_manager
        self.car_model \
            = car_model_manager.draw_car_model_at_random(house_agent.location,
            company.location, self.distance_commuted_if_work_and_home_equal)
        # self.car_model = car_model_manager.car_models[19]
        self.whereabouts = whereabouts_manager.track_new_agent(uid,
                                                               cur_activity,
                                                               cur_location)
        self.soc = self.car_model.battery_capacity \
            * self.parameters.get("start_soc","float")# soc in kWh
        self.charge_at_home = 0.0
        self.charge_at_work = 0.0
        self.charge_held_back = 0.0
        
        self.total_charge = {"GRID": 0, "PV": 0, "WORK": 0, "PUBLIC": 0 }
        
        self.electricity_cost = 0 # in $ i guess ^^
        self.cur_electricity_cost = 0
        self.cp = calendar_planer
        self.calendar = Cal(self.clock, self.lrm, calendar_planer,
                            self.whereabouts, house_agent.location,
                            company.location, cur_activity, cur_location,
                            self.distance_commuted_if_work_and_home_equal)
        
        self.departure_condition = parameters.get("departure_condition",
                                                  "string")
        if self.departure_condition not in {"ROUND_TRIP", "ONE_WAY_TRIP", 
                                            "NEXT_NODE"}:
            raise RuntimeError("car_agent.py: Departure condition: " \
                        + str(self.departure_condition) + " is ill defined!")
        self.reserve_range = parameters.get("reserve_range","int")
        self.reserve_speed = parameters.get("reserve_speed","int")
        self.reserve_power = self.car_model.consumption(self.reserve_speed,
                                                        self.reserve_range)
        self.emergency_charging = 0.0 # in kWh
        self.queuing_condition = parameters.get("queuing_condition", "string")
        if self.queuing_condition not in {"ALWAYS", "WHEN_NEEDED"}:
            raise RuntimeError("car_agent.py: Queuing condition: " \
                + str(self.queuing_condition) + " is ill defined!")
        minimum_relative_state_of_charge \
            = self.parameters.get("minimum_relative_state_of_charge", "float")
        self.minimum_absolute_state_of_charge \
            = self.car_model.battery_capacity*minimum_relative_state_of_charge
        
        self.charging_strategy = ChargingStrategy(parameters, self)
        
        self.would_run_flat = False
        self.extracted_data = extracted_data
        self.last_charge_at_work = 0
        self.activity_before_emergency_charging = None
        self.distance_travelled = 0
        
        self.stop_at = -1
        
    def step(self):
        if self.uid == self.parameters.uid_to_check:
            test = 0
        # initialise extraction data
        self.distance_travelled = 0
        self.cur_electricity_cost = 0
        self.charge_held_back = 0.0
        
        # Writing this while I should be celebrating christmas, fuck COVID
        self.calendar.step()
        self.plan()
        self.move()
        self.extracted_data.set(self.tracking_id, "work_charge_instruction",
                                self.charge_at_work)
        self.extracted_data.set(self.tracking_id, "home_charge_instruction",
                                self.charge_at_home)
        self.extracted_data.set(self.tracking_id,
                                "emergency_charge_instruction",
                                self.emergency_charging)
        self.charge()
        
        cur_soc = self.soc / self.car_model.battery_capacity
        self.extracted_data.set(self.tracking_id, "soc", cur_soc)
        self.extracted_data.set(self.tracking_id, "cur_activity",
                                self.whereabouts.cur_activity)
        self.extracted_data.set(self.tracking_id, "charge_held_back",
                                self.charge_held_back)
        self.last_charge_at_work = self.charge_at_work
        
    def plan(self):
        """ This function determines if the agent should start a new journey
        in this time step and when to charge. """
        if self.uid == self.stop_at:
            test = 0
        # Decide on new destination
        if self.emergency_charging == 0 and not self.whereabouts.is_travelling:
            if self.whereabouts.has_arrived: # Case: Normal departure
                if self.whereabouts.cur_activity == self.calendar.cur_scheduled_activity:
                    if self.calendar.next_departure_time <= self.clock.elapsed_time:
                        if self.uid == self.stop_at:
                            print("\n" + str(self))
                            print("\n" + str(self.whereabouts))
                            test = 0
                        self.whereabouts.set_destination(self.calendar.next_activity,
                                                         self.calendar.next_location,
                                                         self.calendar.next_activity_start_time)
                        if self.uid == self.stop_at:
                            print("\n" + str(self.whereabouts))
                            test = 0
                else: # Case: Delayed departure
                    if self.whereabouts.destination_activity_start_time <= self.clock.elapsed_time:
                        if self.uid == self.stop_at:
                            print("\n" + str(self))
                            print("\n" + str(self.whereabouts))
                            test = 0
                        self.whereabouts.set_destination(self.calendar.cur_scheduled_activity,
                                                         self.calendar.cur_scheduled_location,
                                                         self.calendar.cur_scheduled_activity_start_time)
                        if self.uid == self.stop_at:
                            print("\n" + str(self.whereabouts))
                            test = 0
            else: # Case: After trip interuption
                if self.uid == self.stop_at:
                    test = 0
                self.whereabouts.set_destination(self.whereabouts.destination_activity,
                                                 self.whereabouts.destination_location,
                                                 self.whereabouts.destination_activity_start_time)        
        # provide initial charging instructions
        if self.clock.cur_time_step==1 and not self.whereabouts.is_travelling:
            self.plan_charging()
    
    def move(self):
        """ Process agent's movement, incl. departure- and queuing conditions
        as well as initiating emergency charging and blocking chargers upon
        arrivial."""
        # short hands
        tn = self.lrm.traffic_network
        wa = self.whereabouts
        
        # for wa.is_travelling to be True, cur_loc != scheduled_loc and no
        # emergency charing is required therefore if clauses are omitted
        if not wa.is_travelling:
            return
        # if trip is about to start (that is only directly after route is
        # planned) 
        if wa.cur_location.uid == wa.route[0] \
            and wa.distance_since_last_location == 0:
            self.charge_at_home = 0
            self.charge_at_work = 0
            # if at work make sure to remove oneself from charging que
            self.company.remove_from_charging_que(self)
            if self.company.can_charge(self):
                self.company.unblock_charger(self)
            # check departure condition
            charge_needed = self.charge_for_departure_condition(wa.route)
            if charge_needed > self.soc:
                self.initiate_emergency_charging(charge_needed - self.soc)
                wa.terminate_trip(False)
                return
        # in case of travel within one area only 
        if self.house_agent.location == self.company.location:
            velocity = self.lrm.inner_area_speed_limit
            distance = self.distance_commuted_if_work_and_home_equal
            consumption = self.car_model.consumption(velocity, distance)
            self.distance_travelled  += distance
            self.extracted_data.add(self.tracking_id, "charge_consumed",
                                    consumption)
            self.soc -= consumption
            self.arrival_at_destination()
            return
        
        # time remaining of step in h
        remaining_time = self.clock.time_step / 60
        while remaining_time > 0:
            # short hand critical parameters
            (start, end) = wa.cur_edge
            if start == end:
                #print("\nRoute not valid for Agent {}".format(self.uid))
                self.stop_at = self.uid
                self.calendar.stop_at = self.uid
                print("")
                print(self)
                wa.terminate_trip(True)
                break
            # correct edge
            cur_velocity = tn[start][end]['current_velocity']
            speed_limit = tn[start][end]['speed_limit']
            edge_distance = tn[start][end]['distance']
            possible_distance_on_edge = cur_velocity * remaining_time
            remaining_distance_on_edge \
                = edge_distance - wa.distance_since_last_location
            remaining_time_on_edge = remaining_distance_on_edge / cur_velocity
            # in case of departure from a location check if next location can
            # be reached
            if wa.distance_since_last_location == 0:
                max_consunption_on_edge \
                    = self.car_model.consumption(speed_limit,
                                                 remaining_distance_on_edge)
                # if next location can't be reached determine required
                # emergency charge volume and abort trip
                if self.soc < max_consunption_on_edge:
                    # determine emergency charge volume
                    index_start = wa.route.index(start)
                    # iterate throuh all locations en route starting from
                    # current (start) node and ending with location BEFORE the
                    # final destiantion
                    emergency_charge_volume = 0.0
                    for i, node in enumerate(wa.route[index_start:-1]):
                        prev_node = wa.route[i]
                        next_node = wa.route[i+1]
                        assumed_velocity = tn[prev_node][next_node]\
                                                                ['speed_limit']
                        distance = tn[prev_node][next_node]['distance']
                        assumed_time = distance / assumed_velocity
                        assumed_cons \
                            = self.car_model.instantaneous_consumption(
                                                            assumed_velocity)
                        emergency_charge_volume += assumed_time * assumed_cons
                    self.initiate_emergency_charging(emergency_charge_volume)
                    # abort trip
                    wa.terminate_trip(False)
                    break
            # if next location can be reached during this time step
            if possible_distance_on_edge > remaining_distance_on_edge:
                wa.cur_location = self.lrm.locations[end]
                wa.cur_location_coordinates = wa.cur_location.coordinates()
                consumption = self.car_model.consumption(cur_velocity,
                                                remaining_distance_on_edge)
                self.distance_travelled += remaining_distance_on_edge
                self.extracted_data.add(self.tracking_id, "charge_consumed",
                                        consumption)
                self.soc -= consumption
                # if next location is final destination
                if wa.route[-1] == end:
                    remaining_time = 0
                    self.arrival_at_destination()
                # if next location is not final destination
                else:
                    index_end = wa.route.index(end)
                    wa.cur_edge = (end, wa.route[index_end + 1])
                    remaining_time -= remaining_time_on_edge
                    wa.distance_since_last_location = 0.0
            # if next location can not be reached during this timestep 
            else:
                distance_travelled = remaining_time * cur_velocity
                self.distance_travelled  += distance_travelled
                wa.distance_since_last_location += distance_travelled
                # determine current coordinates
                coord_start = self.lrm.locations[start].coordinates()
                coord_end = self.lrm.locations[end].coordinates()
                ratio_trvld_on_edge = wa.distance_since_last_location \
                                                                / edge_distance
                diff_vct = [coord_end[0] - coord_start[0],
                            coord_end[1] - coord_start[1]]
                wa.cur_location_coordinates = \
                    [coord_start[0] + ratio_trvld_on_edge * diff_vct[0],
                     coord_start[1] + ratio_trvld_on_edge * diff_vct[1]]
                consumption = self.car_model.consumption(cur_velocity,
                                                       distance_travelled)
                self.extracted_data.add(self.tracking_id, "charge_consumed",
                                        consumption)
                self.soc -= consumption
                remaining_time = 0
        # update position on grid
        relative_position \
            =self.lrm.relative_coordinate_position(wa.cur_location_coordinates)
        self.model.space.move_agent(self, relative_position)
        
    def arrival_at_destination(self):
        self.whereabouts.terminate_trip(True)
        self.plan_charging()
        # check if agent has arrived at work and intends to charge at work
        if self.whereabouts.destination_activity == self.cp.WORK \
            and self.charge_at_work != 0:
            # the logic check if a charger is available or if agent has to que
            # for charging happens in company_charger_manager
            is_queuing = None
            if self.queuing_condition == "ALWAYS":
                is_queuing = True
            else: # i.e. if self.queuing_condition == "WHEN_NEEDED"
                is_queuing = self.has_to_charge_prior_to_departure()
            self.company.block_charger(self, is_queuing)
            
    def charge_needed_for_route(self, route):
        """
        Returns the amount of power needed at most for a given route.

        Parameters
        ----------
        route : int[]
            A list of location.uid from start to end location.

        Returns
        -------
        bool
            As per method description.

        """ 
        distances = []
        speed_limits = []
        prev_node = -1
        for cur_node in route:
            if prev_node != -1:
                distances.append(
                    self.lrm.traffic_network[prev_node][cur_node]['distance'])
                speed_limits.append(
                    self.lrm.traffic_network[prev_node][cur_node]\
                                                              ['speed_limit'])
            prev_node = cur_node
        
        expected_consumption = []
        for i, distance in enumerate(distances):
            consumption = self.car_model.consumption(speed_limits[i],
                                                     distance)
            expected_consumption.append(consumption)
        # in case agent works in its home area
        if expected_consumption == []:
            speed_limit = self.lrm.inner_area_speed_limit
            distance = self.distance_commuted_if_work_and_home_equal
            consumption = self.car_model.consumption(speed_limit, distance)
            expected_consumption = [consumption]
        charge_needed = sum(expected_consumption)
        
        # # in case of travel within one area only 
        # if self.house_agent.location == self.company.location:
        #     time_travelled = self.distance_commuted_if_work_and_home_equal \
        #         / self.lrm.inner_area_speed_limit
        #     instant_consumption \
        #         = self.car_model.instantaneous_consumption(\
        #                                        self.lrm.inner_area_speed_limit)
        #     charge_needed = instant_consumption * time_travelled
        
        return charge_needed
            
        
    def charge_for_departure_condition(self, route):
        """
        Checks if the conditions for departure are satisfied.

        Parameters
        ----------
        route : int[]
            A list of location.uid from start to end location.

        Returns
        -------
        bool
            As per method description.

        """
        route_power = self.charge_needed_for_route(route)
        power_required = 0
        if self.departure_condition == "ROUND_TRIP":
            power_required = route_power*2 + self.reserve_power
        if self.departure_condition == "ONE_WAY_TRIP":
            power_required = route_power + self.reserve_power
        
        return power_required
    
    def plan_charging(self):
        self.charge_at_home, self.charge_at_work, self.charge_held_back \
           = self.charging_strategy.determine_charge_instructions(self.soc)
               
    def charge(self):
        """ Charges the EV. """
        if not self.whereabouts.is_travelling \
            and self.soc < self.car_model.battery_capacity:
            cur_activity = self.whereabouts.cur_activity
            cur_location = self.whereabouts.cur_location
            missing_charge =  self.car_model.battery_capacity - self.soc
            total_received_charge = 0.0
            total_charging_cost = 0.0
            # In case of non-emergency charging
            if self.emergency_charging == 0.0:
                # If car agent is at home
                if cur_activity == self.cp.HOME and self.house_agent.is_house:
                    # Determine if the agent should charge already or sill wait 
                    charge_at_home_now = self.charge_at_home
                    if self.charging_strategy.charging_model \
                        == self.charging_strategy.ADVANCED_OVERHAULED_WITH_RISK:
                        charge_at_home_now = 0
                        max_charge_rate \
                            = self.house_agent.max_charge_rate(self.car_model)
                        min_charge_time \
                            = self.charge_at_home / max_charge_rate * 60
                        min_charge_time = self.clock.time_step \
                                * (min_charge_time // self.clock.time_step + 1)
                        if self.calendar.next_departure_time - min_charge_time\
                            <= self.clock.elapsed_time:
                                charge_at_home_now = self.charge_at_home
                    # in case agent can charge from pv and is allowed to always
                    # charge from pv, adapt charge_at_home_now instruction
                    if self.charging_strategy.always_charge_from_pv == True:
                        charge_at_home_now \
                            = max(charge_at_home_now,
                                  min(self.house_agent.max_charge_rate(self.car_model)\
                                      * self.clock.time_step / 60,
                                      self.house_agent.cur_house_power_balance,
                                      self.car_model.battery_capacity * 0.8 \
                                          - self.soc))
                    if charge_at_home_now > 0:
                        charge_up_to = min(charge_at_home_now, missing_charge)
                        received_charge_pv, received_charge_grid, \
                            charging_cost \
                            = self.house_agent.charge_car(self,
                                                          charge_up_to)
                        received_charge \
                            = received_charge_pv + received_charge_grid
                        if self.charge_at_home > 0:
                            self.charge_at_home -= received_charge
                        missing_charge -= received_charge
                        self.soc += received_charge
                        total_received_charge += received_charge
                        total_charging_cost += charging_cost
                        self.extracted_data.add(self.tracking_id,
                                                "charge_received_pv",
                                                received_charge_pv)
                        self.extracted_data.add(self.tracking_id, 
                                                "charge_received_grid",
                                                received_charge_grid)
                # if car agent is at work
                if cur_activity == self.cp.WORK \
                    and self.charge_at_work != 0.0:
                    if self.company.can_charge(self):
                        charge_up_to = min(self.charge_at_work, missing_charge)
                        received_charge, charging_cost \
                            = self.company.charge_car(self, charge_up_to)
                        self.charge_at_work -= received_charge
                        if self.charge_at_work == 0:
                            self.company.unblock_charger(self)
                        self.soc += received_charge
                        total_received_charge += received_charge
                        total_charging_cost += charging_cost
                        self.extracted_data.add(self.tracking_id,
                                                "charge_received_work",
                                                received_charge)
                    elif self not in self.company.ccm.charging_que:
                        is_queuing = None
                        if self.queuing_condition == "ALWAYS":
                            is_queuing = True
                        else: # i.e. if self.queuing_condition == "WHEN_NEEDED"
                            is_queuing = self.has_to_charge_prior_to_departure()
                        self.company.block_charger(self, is_queuing)
                        
            # In case of emergency charging
            else:
                # # if car agent is at home
                # if cur_activity == self.cp.HOME:
                #     received_charge, charging_cost \
                #         = self.house_agent.charge_car(self, 
                #                                       self.emergency_charging)
                #     self.emergency_charging -= received_charge
                #     total_received_charge += received_charge
                #     total_charging_cost += charging_cost
                #     self.extracted_data["charge_received_grid"] \
                #         += received_charge
                # # if car agent is at work
                # elif cur_activity == self.cp.WORK:
                #     if self.company.can_charge(self):
                #         received_charge, charging_cost \
                #             = self.company.charge_car(self,
                #                                       self.emergency_charging)
                #         self.emergency_charging -= received_charge
                #         total_received_charge += received_charge
                #         total_charging_cost += charging_cost
                #         if self.emergency_charging == 0:
                #             self.company.unblock_charger(self)
                #         self.extracted_data["charge_received_work"] \
                #             += received_charge
                # # if car agent has to use public charger whilst in between home
                # # and work
                # else:
                pub_company = cur_location.companies[0]
                if pub_company.can_charge(self):
                    received_charge, charging_cost \
                        = pub_company.charge_car(self,
                                                 self.emergency_charging)
                    self.emergency_charging -= received_charge
                    self.soc += received_charge
                    total_received_charge += received_charge
                    total_charging_cost += charging_cost
                    if self.emergency_charging == 0:
                        pub_company.unblock_charger(self)
                    self.extracted_data.add(self.tracking_id,
                                            "charge_received_public",
                                            received_charge)
                if self.emergency_charging == 0:
                    if self.activity_before_emergency_charging \
                        == self.whereabouts.destination_activity:
                        self.whereabouts.cur_activity \
                            = self.activity_before_emergency_charging
                        self.plan_charging()
            
            self.cur_electricity_cost = total_charging_cost
            self.electricity_cost += total_charging_cost
            
    def initiate_emergency_charging(self, emergency_charge_volume):
        """
        Assigns the emergency charge volume and blocks a charger / ques for 
        charging if needed.

        Parameters
        ----------
        emergency_charge_volume : float
            The amount of electricity required to be charged.

        Returns
        -------
        None.

        """
        # check if charging needs can be satisfied
        if self.soc+emergency_charge_volume <= self.car_model.battery_capacity:
            if self.whereabouts.cur_activity != self.cp.EMERGENCY_CHARGING:
                self.activity_before_emergency_charging \
                    = self.whereabouts.cur_activity
            self.whereabouts.cur_activity = self.cp.EMERGENCY_CHARGING
            # prepare for charging
            # if self.house_agent.location == self.whereabouts.cur_location \
            #     and self.whereabouts.cur_activity == self.cp.HOME:
            #     # well nothting much needs to be done at home as there is one
            #     # charger per car
            #     pass
            # elif self.company.location == self.whereabouts.cur_location \
            #     and self.whereabouts.cur_activity == self.cp.WORK \
            #     and len(self.company.ccm.chargers_not_in_use) != 0:
            #     # charge at place of employment
            #     self.company.block_charger(self, True)
            # else:
            # charge at public charger
            self.whereabouts.cur_location.companies[0].block_charger(self, True)
            self.emergency_charging = emergency_charge_volume
        else:
            # car agent does not depart because it would run flat
            self.would_run_flat = True
    
    def has_to_charge_prior_to_departure(self):
        """
        This function is executed after arrival at a final destination to check
        if the car_agent needs to charge before leaving on the next trip.

        Returns
        -------
        BOOL.
            Returns True or False, that is if the agent needs to charge or not.
        """
        next_route = self.lrm.calc_route(self.whereabouts.cur_location,
                                         self.calendar.next_location)
        if self.charge_for_departure_condition(next_route) < self.soc:
            return True
        else:
            return False           
        
    def generate_calendar_entries(self):
        commute_consumption = self.charge_needed_for_route(\
            self.lrm.calc_route(self.house_agent.location,
                                self.company.location))
        charge_time_at_work \
            = commute_consumption / self.car_model.charger_capacity_ac
        # round up
        if not charge_time_at_work.is_integer():
            charge_time_at_work = charge_time_at_work // 1 + 1
        self.min_shift_length = charge_time_at_work # jup, just for readability
        return self.calendar.generate_schedule(self.min_shift_length)
        
    def calc_forcast_mean_and_std_dev(self, begin_forecast, end_forecast):
        mu_supply, sig_supply \
            = self.house_agent.hgm.generation_forecast_distribution_parameter(\
                    self.house_agent.pv_capacity, begin_forecast, end_forecast)
        mu_demand, sig_demand \
            = self.house_agent.hcm.consumption_forecast_distribution_parameters(\
                        self.house_agent.location, self.house_agent.occupants,
                        begin_forecast, end_forecast)
        
        # mu = mu_supply - mu_demand
        # sig = math.sqrt(sig_supply**2 + sig_demand**2)
        mu, sig_sqr = 0, 0
        for it in range(len(mu_supply)):
            balance = mu_supply[it] - mu_demand[it]
            if mu_supply[it] - mu_demand[it] >= 0:
                mu += balance
                sig_sqr += sig_supply[it]**2 + sig_demand[it]**2
        
        return mu, math.sqrt(sig_sqr)
    
    def __repr__(self):
        c_g = self.extracted_data.sum_over_agent("charge_received_grid",
                                                 self.tracking_id)
        c_pv = self.extracted_data.sum_over_agent("charge_received_pv",
                                                 self.tracking_id)
        c_w = self.extracted_data.sum_over_agent("charge_received_work",
                                                 self.tracking_id)
        c_p = self.extracted_data.sum_over_agent("charge_received_public",
                                                 self.tracking_id)
        msg = "Uid: {}, Residency uid: {}, Employment uid: {} ".format( \
                self.uid, self.house_agent.location.uid,
                self.company.location.uid)
        msg += "SOC: {:.01f}\n ".format(self.soc)
        msg += "Charge Instr. @Home: {:.02f}, @Work: {:.02f}, ".format( \
                self.charge_at_home, self.charge_at_work)
        msg += "Emergency: {:.02f}\n".format( \
                self.emergency_charging)
        msg += "Received charge - Grid: {:.02f}, ".format(c_g)
        msg += "PV: {:.02f}, Work: {:.02f}, Public: {:.02f}\n".format(
                c_pv,c_w, c_p)
        # msg += "Latest History: \n"
        # for time_step, hist in list(self.extracted_data_hist.items())[-3:]:
        #     msg += str(time_step) + " | "
        #     for key in hist.keys():
        #         if key != "whereabouts":
        #             msg += "{}: {:0.2f} ".format(key, hist[key])
        #         else:
        #             msg += "\n" + str(hist[key])
        #     msg+= "\n"
        return msg