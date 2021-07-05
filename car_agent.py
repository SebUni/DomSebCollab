# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 13:06:27 2020

@author: S3739258
"""
import sys
import math
import scipy.special
from scipy.special import erf, erfinv
import scipy.optimize

from mesa import Agent

from cal import Cal

class CarAgent(Agent):
    """An agent which can travel along the map."""
    def __init__(self, uid, model, clock, cur_activity, cur_location,
                 house_agent, company, location_road_manager,
                 car_model_manager, whereabouts_manager, calendar_planer,
                 parameters):
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
        self.parameters = parameters
        self.clock = clock
        self.house_agent = house_agent
        self.company = company
        self.distance_commuted_if_work_and_home_equal \
            = house_agent.location.draw_distance_commuted_if_work_equal_home_at_random()
        # TODO reconsider how car models are chosen
        self.lrm = location_road_manager
        self.car_model = car_model_manager.draw_car_model_at_random()
        self.whereabouts = whereabouts_manager.track_new_agent(uid,
                                                               cur_activity,
                                                               cur_location)
         # TODO check if all agents should start with 100% SOC
        self.soc = self.car_model.battery_capacity # soc in kWh
        self.charge_at_home_from_grid = 0.0
        self.charge_at_home_from_pv = 0.0
        self.charge_at_work = 0.0
        
        self.electricity_cost = 0 # in $
        self.calendar = Cal(self.clock, self.lrm, calendar_planer,
                            self.whereabouts, house_agent.location,
                            company.location, cur_activity, cur_location,
                            self.distance_commuted_if_work_and_home_equal)
        
        self.departure_condition \
            = parameters.get_parameter("departure_condition","string")
        if self.departure_condition not in {"ROUND_TRIP", "ONE_WAY_TRIP", 
                                            "NEXT_NODE"}:
            sys.exit("Departure condition: " + str(self.departure_condition) \
                     + " is ill defined!")
        self.reserve_range = parameters.get_parameter("reserve_range","int")
        self.reserve_speed = parameters.get_parameter("reserve_speed","int")
        self.emergency_charging = 0.0 # in kWh
        self.queuing_condition = parameters.get_parameter("queuing_condition",
                                                          "string")
        if self.queuing_condition not in {"ALWAYS", "WHEN_NEEDED"}:
            sys.exit("Queuing condition: " + str(self.queuing_condition) \
                     + " is ill defined!")
        self.would_run_flat = False
        
    def step(self):
        # Writing this while I should be celebrating christmas, fuck COVID
        self.plan()
        self.move()
        self.charge()
        self.calendar.step()
        
    def plan(self):
        """ This function determines if the agent should start a new journey
        in this time step and when to charge. """
        # Decide on new destination
        if self.calendar.upcoming_departure_time <= self.clock.elapsed_time:
            if self.emergency_charging == 0.0 \
                and not self.whereabouts.is_travelling:
                self.whereabouts.set_destination(self.calendar.next_location)
        # Decide on when to charge
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
        # planned) check departure condition
        if wa.cur_location.uid == wa.route[0] \
            and wa.distance_since_last_location == 0:
            charge_needed = self.charge_for_departure_condition(wa.route)
            if charge_needed > self.soc:
                self.initiate_emergency_charging(charge_needed - self.soc)
                wa.terminate_trip()
                return
        # in case of travel within one area only 
        if self.house_agent.location == self.company.location:
            time_travelled = self.distance_commuted_if_work_and_home_equal \
                / self.lrm.inner_area_speed_limit
            instant_consumption \
                = self.car_model.instantaneous_consumption(\
                                               self.lrm.inner_area_speed_limit)
            self.soc -= instant_consumption * time_travelled
            self.arrival_at_destination()
            return
        
        # time remaining of step in h
        remaining_time = self.clock.time_step / 60
        while remaining_time > 0:
            # short hand critical parameters
            (start, end) = wa.cur_edge
            # correct edge 
            cur_velocity = tn[start][end]['current_velocity']
            speed_limit = tn[start][end]['speed_limit']
            edge_distance = tn[start][end]['distance']
            possible_distance_on_edge = cur_velocity * remaining_time
            remaining_distance_on_edge \
                = edge_distance - wa.distance_since_last_location
            remaining_time_on_edge = remaining_distance_on_edge / cur_velocity
            inst_consumption \
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
                self.soc -= remaining_time_on_edge * inst_consumption
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
                wa.distance_since_last_location \
                    += remaining_time * cur_velocity
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
                self.soc -= remaining_time * inst_consumption
                remaining_time = 0
        # update position on grid
        relative_position \
            =self.lrm.relative_coordinate_position(wa.cur_location_coordinates)
        self.model.space.move_agent(self, relative_position)
        
    def arrival_at_destination(self):
        self.whereabouts.cur_activity = self.calendar.next_activity
        self.whereabouts.terminate_trip()
        self.plan_charging()
        # check if agent has arrived at work and intends to charge at work
        if self.company.location ==self.whereabouts.cur_location \
            and self.charge_at_work != 0:
            # the logic check if a charger is available or if agent has to que
            # for charging happens in company_charger_manager
            is_queuing = None
            if self.queuing_condition == "ALWAYS":
                is_queuing = True
            else: # i.e. if self.queuing_condition == "WHEN_NEEDED"
                is_queuing = self.has_to_charge_prior_to_departure()
            self.company.block_charger(self, is_queuing)
        
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
            expected_consumption.append(instant_consumption * time_on_segment)
        # in case agent works in its home area
        if expected_consumption == []:
            time_on_segment = self.distance_commuted_if_work_and_home_equal \
                / self.lrm.inner_area_speed_limit
            instant_consumption \
                = self.car_model.instantaneous_consumption(\
                                               self.lrm.inner_area_speed_limit)
            expected_consumption.append(instant_consumption * time_on_segment)
            
        reserve_power \
            = self.car_model.instantaneous_consumption(self.reserve_speed)
        
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
        if not self.whereabouts.is_travelling \
            and self.soc < self.car_model.battery_capacity:
            cur_location = self.whereabouts.cur_location
            missing_charge =  self.car_model.battery_capacity - self.soc
            received_charge = 0.0
            charging_cost = 0.0
            # In case of non-emergency charging
            if self.emergency_charging == 0.0:
                # If car agent is at home
                if cur_location == self.house_agent.location:
                    total_charge_cur_time_step = 0
                    # First try to charge from pv
                    if self.charge_at_home_from_pv != 0:
                        max_from_pv = self.house_agent.cur_pv_excess_supply
                        charge_up_to = min(self.charge_at_home_from_pv,
                                           missing_charge, max_from_pv)
                        received_charge, charging_cost \
                            = self.house_agent.charge_car(self, charge_up_to)
                        self.charge_at_home_from_pv \
                            = self.charge_at_home_from_pv - received_charge
                        self.house_agent.cur_pv_excess_supply -= received_charge
                        total_charge_cur_time_step = received_charge
                    if self.charge_at_home_from_grid != 0:
                        charger_capacity_in_time_step \
                            = self.house_agent.max_charge_rate(self.car_model)\
                                * self.clock.time_step / 60
                        remaining_charger_capacity \
                            = charger_capacity_in_time_step \
                              - total_charge_cur_time_step
                        charge_up_to = min(self.charge_at_home_from_grid,
                                           missing_charge,
                                           remaining_charger_capacity)
                        received_charge, charging_cost \
                            = self.house_agent.charge_car(self, charge_up_to)
                        self.charge_at_home_from_grid \
                            = self.charge_at_home_from_grid - received_charge
                # if car agent is at work
                if cur_location == self.company.location \
                    and self.charge_at_work != 0.0 \
                    and self.company.can_charge(self):
                    charge_up_to = min(self.charge_at_work, missing_charge)
                    received_charge, charging_cost \
                        = self.company.charge_car(self, charge_up_to)
                    self.charge_at_work -= received_charge
                    if self.charge_at_work == 0:
                        self.company.unblock_charger(self)
            # In case of emergency charging
            else:
                # if car agent is at home
                if cur_location == self.house_agent.location:
                    received_charge, charging_cost \
                        = self.house_agent.charge_car(self, 
                                                      self.emergency_charging)
                    self.emergency_charging -= received_charge
                # if car agent is at work
                elif cur_location == self.company.location:
                    if self.company.can_charge(self):
                        received_charge, charging_cost \
                            = self.company.charge_car(self,
                                                      self.emergency_charging)
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
                                                     self.emergency_charging)
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
            elif self.company.location == self.whereabouts.cur_location:
                # charge at place of employment
                self.company.block_charger(self, True)
            else:
                # charge at public charger
                self.location.companies[0].block_charger(self, True)
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
        charge_needed = self.charge_for_departure_condition(next_route)
        if charge_needed < self.soc:
            return True
        else:
            return False           
        
    def generate_calendar_entries(self):
        self.calendar.generate_schedule()
    
    def plan_charging(self):
        p_work = self.company.charger_cost_per_kWh
        p_feed = self.house_agent.electricity_plan.feed_in_tariff
        p_grid = self.house_agent.electricity_plan.cost_of_use(1, 
                                                        self.clock.time_of_day)
        
        p_em = self.parameters.get_parameter("public_charger_cost_per_kWh",
                                             "float")
        
        soc = self.soc
        q_one_way = self.lrm.calc_route_length(self.calendar.next_route)
        
        c = self.parameters.get_parameter("confidence", "float")
        mu_supply, sig_supply \
            = self.house_agent.hgm.generation_forecast_distribution_parameter()
        mu_demand, sig_demand \
            = self.house_agent.hcm.consumption_forecast_distribution_parameters()
        
        mu = mu_supply - mu_demand
        sig = math.sqrt(sig_supply**2 + sig_demand**2)
        
        if self.whereabouts.cur_location == self.company.location:
            # q_home \
            #     = scipy.optimize.minimize_scalar(self.parm_cost_fct_charging_at_work,
            #         args=(q_one_way, p_em, p_feed, p_grid, p_work, soc, c, mu,
            #               sig),
            #         bounds=((0, q_one_way),)).x
            # self.charge_at_work = max(2 * q_one_way - soc - q_home, 0)
            self.charge_at_work \
                 = self.parm_cost_fct_charging_at_work_anal(q_one_way, p_feed, 
                                                           p_grid, p_em,
                                                           p_work, soc, c, mu,
                                                           sig)
            
        
        if self.whereabouts.cur_location == self.house_agent.location:
#            self.charge_at_home_from_pv \
#                = scipy.optimize.minimize_scalar(self.parm_cost_fct_charging_at_home,
#                    args=(q_one_way, p_em, p_feed, p_grid, p_work, soc, c, mu,
#                          sig),
#                    bounds=((0, q_one_way),)).x
            self.charge_at_home_from_pv \
                = self.parm_cost_fct_charging_at_home_anal(q_one_way, p_feed, 
                                                           p_grid, p_em,
                                                           p_work, soc, c, mu,
                                                           sig)
            max_charge_rate \
                = self.house_agent.max_charge_rate(self.car_model)
            if p_em > p_work and p_em > p_grid:
                charge_needed \
                    = max(2 * q_one_way - soc, 0) if p_grid <= p_work \
                        else max( q_one_way - soc, 0)
                min_charge_time = charge_needed / max_charge_rate * 60
                min_charge_time = (min_charge_time // self.clock.time_step) \
                        * self.clock.time_step
                if self.clock.elapsed_time \
                    <= self.calendar.upcoming_departure_time - min_charge_time \
                    < self.clock.elapsed_time + self.clock.time_step:
                    self.charge_at_home_from_grid = charge_needed;
            else:
                msg = "Case p_em <= p_work || p_em <= p_grid not implemented"
                sys.exit(msg)
    
    """
    PARAMETER EXPLANATION
    
    q_h (q_home) 
        quantity charged at home
    q_ow (q_one_way)
        charge needed to reach next destination
    q_r (q_real)
        realisation of the house demand-supply-'balance'
    q_w (q_work)
        quantity charged at work
    p_w (p_work)
        price paid per kWh at work
    p_f (p_feed)
        price received for feeding rooftop pv into grid
    p_g (p_grid)
        price paid per kWh at home
    p_em (p_emergency)
        most expensive price paid on the road to next to charging in case of
        emergency charging
    soc
        state of charge of the EV's battery
    c
        confidence with which best cases are expected
    mu
        mean for predicition of rooftop pv output
    sig
        standard deviation for predicition of rooftop pv output
    phi
        value at risk
    """
    
    # TODO update in draw.io ClassDiagram
    
    def parm_cost_fct_charging_at_home(self, q_h, q_ow, p_em, p_f, p_g, p_w, 
                                       soc, c, mu, sig):
        q_w = max(2 * q_ow - soc - q_h, 0)
        return self.cost_fct_charging_at_home(q_h, q_ow, q_w, p_f, p_g, p_em, 
                                              p_w, soc, c, mu, sig)
    
    def cost_fct_charging_at_home(self, q_h, q_ow, q_w, p_f, p_g, p_em, p_w,
                                  soc, c, mu, sig):
        p = lambda value : max(value, 0)
        return q_w * p_w + q_h * p_f \
          + (p(q_ow - soc - q_h) + p(q_ow - p(soc + q_h - q_ow) - q_w)) * p_em\
          + self.CVaR(q_h, c, mu, sig, p_f, p_g)
    
    def parm_cost_fct_charging_at_work(self, q_h, q_ow, p_em, p_f, p_g, p_w, 
                                       soc, c, mu, sig):
        q_w = max(2 * q_ow - soc - q_h, 0)
        return self.cost_fct_charging_at_work(q_h, q_ow, q_w, p_f, p_g, p_em, 
                                              p_w, soc, c, mu, sig)
    
    def cost_fct_charging_at_work(self, q_h, q_ow, q_w, p_f, p_g, p_em, p_w,
                                  soc, c, mu, sig):
        p = lambda value : max(value, 0)
        return q_w * p_w + q_h * p_f \
          + (p(q_ow - soc - q_w) + p(q_ow - p(soc + q_w - q_ow) - q_h)) * p_em\
          + self.CVaR(q_h, c, mu, sig, p_f, p_g)
          
    def CVaR(self, q_h, c, mu, sig, p_f, p_g):
        delta_p = p_g + p_f
        VaR = max(delta_p * (q_h - mu - math.sqrt(2) * sig \
                               * scipy.special.erfinv(1 - 2* c)), 0.0)
        psi = q_h - mu - VaR / delta_p
        return delta_p                                                     \
            * (                                                            \
                q_h - psi - mu                                             \
                + (1 / (1 - c)) * (                                        \
                                   (psi / 2)                               \
                                   * (math.erf(psi / (math.sqrt(2) * sig)) \
                                      + 1)                                 \
                                    + sig**2 * self.N(psi, 0, sig)         \
                                  )                                        \
              )
    
    def N(self, x, mu, sig):
        ''' Normal distribution evaluated at x. '''
        pre_fac = 1/math.sqrt(2*math.pi)
        return (pre_fac / sig) * math.exp( - (x - mu)**2 / (2 * sig**2))
    
    def parm_cost_fct_charging_at_home_anal(self, q_ow, p_f, p_g, p_em, p_w,
                                            soc, c, mu, sig):
        q_tw, q_th = q_ow, q_ow
        sqrt2sig = math.sqrt(2) * sig
        # performance helper
        thresh = mu + sqrt2sig * erfinv(1 - 2*c)
        # shorthands
        dp = p_g - p_f
        dp_div = dp / (2 * (1 - c))
        
        if thresh < q_tw - soc:
            if p_g < p_w:
                return q_tw + q_th - soc
            elif p_g == p_w:
                return q_tw - soc
            else:
                return q_tw - soc
        elif q_tw + q_th - soc < thresh:
            if p_w <= p_f + dp_div * (erf((q_tw - soc - mu) / sqrt2sig) + 1):
                return q_tw - soc
            elif p_w >= p_f + dp_div * (erf((q_tw + q_th - soc - mu) / sqrt2sig) + 1):
                return q_tw + q_th - soc
            else:
                return sqrt2sig * erfinv((p_w - p_f) / dp_div - 1) + mu
        else:
            if p_w > p_g:
                return q_tw + q_th - soc
            elif p_w == p_g:
                return q_tw + q_th - soc
            elif p_f + dp_div * (erf((q_tw - soc - mu) / sqrt2sig) + 1) < p_w < p_g:
                return sqrt2sig * erfinv((p_w - p_f) / dp_div - 1) + mu
            else:
                return q_tw - soc
    
    def parm_cost_fct_charging_at_work_anal(self, q_ow, p_f, p_g, p_em, p_w,
                                            soc, c, mu, sig):
        q_tw, q_th = q_ow, q_ow
        sqrt2sig = math.sqrt(2) * sig
        # performance helper
        thresh = mu + sqrt2sig * erfinv(1 - 2*c)
        # shorthands
        dp = p_g - p_f
        dp_div = dp / (2 * (1 - c))
        
        if q_tw < thresh:
            if p_w >= p_f + dp_div * (erf((q_tw - mu) / sqrt2sig) + 1):
                return q_th - soc
            elif p_w <= p_f + dp_div * (1 - erf(mu / sqrt2sig)):
                return q_th + q_tw - soc
            else:
                return q_th + q_tw - soc - mu \
                    - sqrt2sig * erfinv((p_w - p_f) / dp_div - 1)
        elif thresh < 0:
            if p_g < p_w:
                return q_th - soc
            elif p_g == p_w:
                return q_th - soc
            else:
                return q_th + q_tw - soc
        else:
            if p_w < p_g:
                return q_th + q_tw - soc
            elif p_w == p_g:
                return q_th - soc
            elif p_f + dp_div * (erf(q_tw - mu) / sqrt2sig + 1) > p_w > p_g:
                return q_th + q_tw - soc - mu \
                    - sqrt2sig * erfinv((p_w - p_f) / dp_div - 1)
            else:
                return q_th - soc