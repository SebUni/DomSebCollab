# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 13:06:27 2020

@author: S3739258
"""
import sys

from mesa import Agent

class CarAgent(Agent):
    """An agent which can travel along the map."""
    def __init__(self, uid, model, clock, cur_location, house_agent, company,
                 location_road_manager, car_model_manager, whereabouts_manager,
                 calendar, departure_condition, reserve_range,
                 queuing_condition):
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
            The object handling all car models created in ChargingModel class
        whereabouts_manager : WhereaboutsManager
            The object handling all whereabouts created in ChargingModel class
        calendar: {int, Location}
            Holds the Locations where an agent shall go or be for each time
            slot of one week.
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
        self.clock = clock
        self.house_agent = house_agent
        self.company = company
        # TODO reconsider how car models are chosen
        self.lrm = location_road_manager
        self.car_model = car_model_manager.draw_car_model_at_random()
        self.whereabouts = whereabouts_manager.track_new_agent(uid,
                                                               cur_location)
         # TODO check if all agents should start with 100% SOC
        self.soc = self.car_model.battery_capacity # soc in kWh
        self.charge_at_home = 0.0
        self.charge_at_work = 0.0
        
        self.electricity_cost = 0 # in $
        self.calendar = calendar
        if departure_condition not in {"ROUND_TRIP", "ONE_WAY_TRIP", 
                                       "NEXT_NODE"}:
            sys.exit("Departure condition: " + str(departure_condition) \
                     + " is ill defined!")
        self.departure_condition = departure_condition
        self.reserve_range = reserve_range
        self.reserve_speed = 100 # in km/h
        self.emergency_charging = 0.0 # in kWh
        if departure_condition not in {"ALWAYS", "WHEN_NEEDED"}:
            sys.exit("Queing condition: " + str(queuing_condition) \
                     + " is ill defined!")
        self.queuing_condition = queuing_condition
        
    def step(self):
        # Writing this while I should be celebrating christmas, fuck COVID
        self.plan()
        self.move()
        self.charge()
        
    def plan(self):
        """ This function determines if the agent should start a new journey
        in this time step and when to charge. """
        # Decide on new destination
        scheduled_loc = self.calendar[self.clock.time_of_week]
        if self.whereabouts.cur_location != scheduled_loc:
            if self.emergency_charging == 0.0:
                if not self.whereabouts.is_traveling:
                    self.whereabouts.set_destination(scheduled_loc)
        # Decide on when to charge
        # TODO implement this properly
        self.charge_at_home = self.car_model.battery_capacity - self.soc
        self.charge_at_work = self.car_model.battery_capacity - self.soc
                    
    
    def move(self):
        """ Process agent's movement, incl. departure- and queuing conditions
        as well as initiating ermergency charging and blocking chargers upon
        arrivial."""
        # short hands
        tn = self.lrm.traffic_network
        wa = self.whereabouts
        # for wa.is_traveling to be True, cur_loc != scheduled_loc and no
        # emergency charing is required therefore if clauses are omitted
        if not wa.is_traveling: return
        # if trip is about to start (that is only directly after route is
        # planned) check departure condition
        if wa.distance_travelled == 0:
            charge_needed = self.charge_for_departure_conditiond(wa.route)
            if charge_needed > self.soc:
                self.initiate_emergency_charging(charge_needed - self.soc)
                wa.terminate_trip()
        
        # time remaining of step in h
        remaining_time = self.clock.time_step / 60
        while remaining_time > 0:
            # short hand critical parameters
            (start, end) = wa.cur_edge
            cur_velocity = tn[start][end]['current_velocity']
            speed_limit = tn[start][end]['speed_limit']
            edge_distance = tn[start][end]['distance']
            possible_distance_on_edge = cur_velocity * remaining_time
            remaining_distance_on_edge \
                = edge_distance - wa.distance_since_last_location
            remaining_time_on_edge = edge_distance / cur_velocity
            cur_consumption \
                = self.car_model.instantaneous_consumption(cur_velocity)
            # in case of departure from a location check if next location can
            # be reached
            if wa.distance_since_last_location == 0:
                max_consunption_on_edge \
                    = self.car_model.instantaneous_consumption(speed_limit)
                # if next location can't be reached determine required
                # emergency charge volume and abort trip
                if self.soc < max_consunption_on_edge * remaining_time_on_edge:
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
                    wa.terminate_trip()
                    break
            # if next location can be reached during this time step
            if possible_distance_on_edge > remaining_distance_on_edge:
                wa.cur_location = self.lrm.locations[end]
                wa.cur_location_coordinates = wa.cur_location.coordinates()
                # if next location is final destination
                if wa.route[-1] == end:
                    wa.cur_edge = (end, end)
                    wa.terminate_trip()
                    remaining_time = 0
                    # check if agent has arrived at work and intends to charge
                    # at work
                    if self.company.location == wa.cur_location \
                        and self.charge_at_work != 0:
                        # the logic check if a charger is available or if agent
                        # has to que for charging happens in
                        # company_charger_manager
                        is_queuing = True if self.queuing_condition else False
                        self.company.block_charger(self, is_queuing)
                # if next location is not final destination
                else:
                    index_end = wa.route.index(end)
                    wa.cur_edge = (end, wa.route[index_end + 1])
                    remaining_time -= remaining_time_on_edge
                    wa.distance_since_last_location = 0.0
                self.soc -= remaining_time_on_edge * cur_consumption
            # if next location can not be reached during this timestep 
            else:
                wa.distance_since_last_location \
                    += self.clock.time_step / 60 * cur_velocity
                self.soc -= self.clock.time_step / 60 * cur_consumption
                # determine current coordinates
                coord_start = self.lrm.locations[start].cooridnates()
                coord_end = self.lrm.locations[end].cooridnates()
                ratio_trvld_on_edge = wa.distance_since_last_location \
                                                                / edge_distance
                diff_vct = [coord_end[0] - coord_start[0],
                            coord_end[1] - coord_start[1]]
                wa.cur_location_coordinates = \
                    [coord_start[0] + ratio_trvld_on_edge * diff_vct[0],
                     coord_end[1] + ratio_trvld_on_edge * diff_vct[1]]
        # update position on grid
        self.model.grid.move_agent(self, wa.cur_location_coordinates)
        
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
            time_on_segment = distance / speed_limits[i]
            instant_consumption \
                = self.car_model.instantaneous_consumption(speed_limits[i])
            expected_consumption.append[instant_consumption * time_on_segment]
        
        reserve_power = self.car_model.instant_consumption(self.reserve_speed)
        
        power_required = 0
        if self.departure_condition == "ROUND_TRIP":
            power_required = sum(expected_consumption)*2 + reserve_power
        if self.departure_condition == "ONE_WAY_TRIP":
            power_required = sum(expected_consumption) + reserve_power
        if self.departure_condition == "NEXT_NODE":
            power_required = expected_consumption[0] + reserve_power
        
        return power_required
            
        
    def charge(self):
        """ Charges the EV. """
        if not self.whereabouts.is_traveling \
            and self.soc < self.car_model.battery_capacity:
            cur_location = self.whereabouts.current_location
            missing_charge =  self.car_model.battery_capacity - self.soc
            received_charge = 0.0
            charging_cost = 0.0
            # In case of non-emergency charging
            if self.emergency_charging == 0.0:
                # If car agent is at home
                if cur_location == self.house_agent.location \
                    and self.charge_at_home != 0.0:
                    charge_up_to = min(self.charge_at_home, missing_charge)
                    received_charge, charging_cost \
                        = self.house_agent.charge_car(charge_up_to,
                                            self.car_model.charger_capacity)
                    self.charge_at_home -= received_charge
                # if car agent is at work
                if cur_location == self.company.location \
                    and self.charge_at_work != 0.0 \
                    and self.company.can_charge(self):
                    charge_up_to = min(self.charge_at_work, missing_charge)
                    received_charge, charging_cost \
                        = self.company.charge_car(self, charge_up_to,
                                            self.car_model.charger_capacity)
                    self.charge_at_work -= received_charge
                    if self.charge_at_work == 0:
                        self.company.unblock_charger(self)
            # In case of emergency charging
            else:
                # if car agent is at home
                if cur_location == self.house_agent.location:
                    received_charge, charging_cost \
                        = self.house_agent.charge_car(self.emergency_charging,
                                            self.car_model.charger_capacity)
                    self.emergency_charging -= received_charge
                # if car agent is at work
                elif cur_location == self.company.location:
                    if self.company.can_charge(self):
                        received_charge, charging_cost \
                            = self.company.charge_car(self,
                                            self.emergency_charging,
                                            self.car_model.charger_capacity)
                        self.emergency_charging -= received_charge
                        if self.emergency_charging == 0:
                            self.company.unblock_charger(self)
                # if car agent has to use public charger whilst in between home
                # and work
                else:
                    pub_company = cur_location.companies[0]
                    if pub_company.can_charge(self):
                        received_charge, charging_cost \
                            = pub_company.charge_car(self,
                                            self.emergency_charging,
                                            self.car_model.charger_capacity)
                        self.emergency_charging -= received_charge
                        if self.emergency_charging == 0:
                            pub_company.unblock_charger(self)
                    
            self.soc += received_charge
            self.electricity_cost += charging_cost
            
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
            # prepare for charging
            if self.house_agent.location == self.whereabouts.cur_location:
                # well nothting much needs to be done at home as there is one
                # charger per car
                pass
            elif self.company.location == self.whereabouts.location:
                # charge at place of employment
                self.company.block_charger(self, True)
            else:
                # charge at public charger
                self.location.companies[0].block_charger(self, True)
            self.emergency_charging = emergency_charge_volume
        else:
            # TODO figure out what to do with cars that can not satisfy their
            # departure criterion in like ... you know .. ever
            pass
    
    def find_next_location(self):
        """
        Finds the next planned location different from the current location.

        Returns
        -------
        next_location : Location
            See description above.

        """
        next_location = self.whereabouts.cur_location
        checked_ts = self.clock.time_of_week
        while self.whereabouts.cur_location == next_location:
            checked_ts += self.clock.time_step
            if checked_ts >= 60*24*7:
                checked_ts = checked_ts % 60*24*7
            next_location = self.calendar[checked_ts]
        return next_location