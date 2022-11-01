"""
Solves the Vericle Routing Problem (VRP) using Column Generation (CG) based on the work of Sean Kelley.
* Defines input and output data requirements
* Builds in-memory dataset
* Defines base class, VRP, for data input and validation
* Defines subclass, HeuristicVRP, for solving VRP with column generation
"""

from ortools.linear_solver import pywraplp
import os
from ticdat.jsontd import make_json_dict
import time
from typing import Tuple, Any, Union

from pyVrp.helpers import input_schema, solution_schema, toy_input, route_is_feasible
from pyVrp.instance_reader import Instance
from pyVrp.initial_solutions import initial_solution


class VRP:
    def __init__(self, input_pth: str = None, solution_path: str = None,
                 input_dict: dict[str, dict[str, Any]] = None, solution_dict=False, initial_solution_type='singleton',
                 mip_solver='CBC', max_count_no_improvements=10):
        """Base constructor for VRP. Checks the validity of the input data and
        solution path. Assigns common attributes.
        :param input_pth: The location of the directory of CSV's storing input data
        :param solution_path: The location of the directory of CSV's where solution data written
        :param input_dict: Dictionary storing input data
        :param solution_dict: Whether or not to return solution data as a dictionary
        """
        assert solution_path or solution_dict, 'must specify where to save solution'
        if solution_path:
            assert os.path.isdir(os.path.dirname(solution_path)), \
                'the parent directory of solution_path must exist'

        # assign base class attributes
        self.solution_path = solution_path
        self.initial_solution_type = initial_solution_type
        self.mip_solver = mip_solver
        self.max_count_no_improvements = max_count_no_improvements
        self.routes = None
        t0 = time.time()
        dat = self._data_checks(input_pth, input_dict)
        self.dat = dat
        print(f"Data Checks done in {round(time.time() - t0, 1)} seconds")
        self.parameters = input_schema.create_full_parameters_dict(dat)
        self.depot_idx = [i for i, f in self.dat.nodes.items() if f['type'] == 'depot'].pop()
        self.fleet = list(range(self.parameters['fleet_size']))
        self.M = max(dat.nodes[i]['close'] + f['travel_time'] + dat.nodes[i]['service_time'] - dat.nodes[i]['open']
                     for (i, j), f in dat.arcs.items()) + 1
        self.infinity = pywraplp.Solver.infinity()

    @staticmethod
    def _data_checks(input_pth: str = None, input_dict: dict[str, dict[str, Any]] = None) -> \
            input_schema.TicDat:
        """ Read in data used for solving this VRP instance. Confirms the data
        match the schema defined in schemas.input_schema. Check that the data
        match the remaining assumptions of our VRP models.
        :param input_pth: The directory containing the CSV's of input data for this VRP instance
        :param input_dict: Dictionary storing input data
        :return: a TicDat containing our input data
        """
        assert input_pth or input_dict, 'must specify an input'
        if input_pth:
            assert os.path.isdir(input_pth), 'input_pth must be a valid directory'

        # read in and do basic data checks
        if input_pth:
            pk_fails = input_schema.csv.find_duplicates(input_pth)
            dat = input_schema.csv.create_tic_dat(input_pth)
        else:
            pk_fails = {}
            dat = input_schema.TicDat(**input_dict)
        fk_fails = input_schema.find_foreign_key_failures(dat)
        check_fails = input_schema.find_data_row_failures(dat)
        type_fails = input_schema.find_data_type_failures(dat)
        assert not pk_fails and not fk_fails and not check_fails and not type_fails, \
            "The following data failures were found: \n" \
            f"Type Constraint: {len(type_fails)}, Check Constraint: {len(check_fails)}, " \
            f"Primary Key: {len(pk_fails)}, Foreign Key: {len(fk_fails)}, "

        # advanced data checks
        for i, node in dat.nodes.items():
            if i > 0:
                assert dat.arcs[0, i]['travel_time'] + node['service_time'] <= node['close'], f'Node {i} is not possible to handle with VRP. Node: {node}'

        p = input_schema.create_full_parameters_dict(dat)
        assert len([f for f in dat.nodes.values() if f['type'] == 'depot']) == 1, \
            "There can only be one depot amongst the nodes"
        assert not [f for f in dat.orders.values() if f['weight'] > p['truck_capacity']], \
            "No order can weigh more than truck capacity"
        assert len(dat.nodes) - len(dat.orders) == 1, \
            "There should be exactly one order for each customer"

        return dat


class HeuristicVRP(VRP):

    def __init__(self, **kwargs):
        """Constructor for heuristic VRP, which uses column generation to create
        a set of covering routes before selecting a good subset of them. Builds
        master and pricing models in gurobi.
        :param **kwargs: keyword arguments to pass onto base constructor
        """
        self.time_start = time.time()
        super().__init__(**kwargs)

        self.model, self.z, self.c, self.routes, self.route_costs = \
            self._create_master_problem(solver_id='GLOP', initial_solution_tyoe=self.initial_solution_type)
        self.sub_model, self.sub_model_params, self.x, self.s = self._create_subproblem()
        self.init_time = time.time() - self.time_start
        self.final_model_status = None

    @staticmethod
    def _print_routes(routes):
        print('routes:')
        for route_idx, route in routes.items():
            print([node['node_idx'] for _, node in route.items()], f'route_idx: {route_idx}')
        return [[node['node_idx'] for _, node in route.items() if node['node_idx']!=0] for route_idx, route in routes.items()]

    def _create_master_problem(self, solver_id='GLOP', initial_solution_tyoe='tw_compatibility_a_la_niko') -> \
            Tuple[pywraplp.Solver, dict[int, pywraplp.Variable], dict[int, pywraplp.Variable],
                  dict[int, dict[int, dict[str, Any]]], dict[int, float]]:
        """ Create the gurobi model for the restricted set covering problem. Will
        eventually select a collection of routes that fulfill all customer orders.
        Begins as an LP to yield dual values for pricing problem. Once all desired
        routes (columns) have been added, variables can be made binary to select
        the most cost efficient subset.
        :return: mdl, z, c, and route, which are respectively the master problem
        gurobi model, dictionary of variables representing which routes are selected,
        a dictionary of the model's constraints, and a dictionary of the stop order
        and arrival times for each route represented in the model.
        """
        # make model
        model = pywraplp.Solver.CreateSolver(solver_id=solver_id)

        if self.routes is not None:
            routes = self.routes
            route_costs = self.route_costs
        if solver_id == 'GLOP':
            if self.routes is None and initial_solution_tyoe == 'singleton':
                # order of stops in the route represented by each variable
                # initialize to be the set of singleton routes (i.e. travel from depot to one customer and back)

                # map a route index to the customer node for each singleton route
                singleton = dict(enumerate(self.dat.orders.keys()))

                routes = {route_idx: {
                    0: {'node_idx': self.depot_idx, 'arrival': 0},
                    1: {'node_idx': j, 'arrival': max(self.dat.arcs[self.depot_idx, j]['travel_time'],
                                                      self.dat.nodes[j]['open'])},
                    2: {'node_idx': self.depot_idx, 'arrival': 24}
                } for route_idx, j in singleton.items()}
                route_costs = {
                    route_idx: self.dat.arcs[self.depot_idx, j]['cost'] + self.dat.arcs[j, self.depot_idx]['cost']
                    for route_idx, j in singleton.items()}
            elif self.routes is None and initial_solution_tyoe == 'tw_compatibility_a_la_niko':
                t0 = time.time()
                arcs = self.dat.arcs
                routes_, self.tw_compability = initial_solution(self.dat.nodes, arcs, self.dat.orders,
                                                                self.dat.parameters['fleet_size']['value'],
                                                                self.dat.parameters['truck_capacity']['value'])
                route_costs = {i: 0 for i in range(len(routes_))}
                routes = {i: dict() for i in range(len(routes_))}
                for route_idx, route in routes_.items():
                    for i, customer in enumerate(route):  # i, customer in enumerate(route)
                        if i == 0:
                            last_customer = 0
                            route_costs[route_idx] += arcs[last_customer, customer]['cost']
                            routes[route_idx][i] = dict(node_idx=self.depot_idx)
                            routes[route_idx][i+1] = dict(node_idx=customer)
                        if 0 < i < len(route):
                            last_customer = route[i-1]
                            # todo, changes here! See if it works
                            route_costs[route_idx] += arcs[last_customer, customer]['cost']
                            routes[route_idx][i + 1] = dict(node_idx=customer)
                            # if route_idx == 4:
                            #    a=2
                        if i == len(route) - 1:
                            last_customer = customer
                            customer = 0
                            route_costs[route_idx] += arcs[last_customer, customer]['cost']
                            routes[route_idx][i + 2] = dict(node_idx=customer)
                print(f'Initial Solution Calculated in {round(time.time() - t0, 2)} seconds')
            elif self.routes is not None:
                pass
            else:
                assert False, 'You need to specify correct \'initial_solution_tyoe\''
            # create variables and set objective
            # z_i - if route i is chosen - begins relaxed for column generation
            z = {route_idx: model.NumVar(name=f'z_{route_idx}', lb=0, ub=1)
                 for route_idx, route in routes.items()}
        else:  # we want MIP model with integer z variables
            z = {route_idx: model.BoolVar(name=f'z_{route_idx}')
                 for route_idx, route in routes.items()}
        # set constraints
        # 8) each customer must be visited by a route (i.e. have delivery demand met)
        # since starting routes are singletons, each must be selected to cover
        c = {j: model.Add(model.Sum([sum([j in [x['node_idx'] for x in route.values()]]) * z[route_idx]
                                     for route_idx, route in routes.items()]) >= 1)
             for j in self.dat.orders}

        return model, z, c, routes, route_costs

    def _create_subproblem(self) -> Tuple[pywraplp.Solver, pywraplp.MPSolverParameters,
                                          dict[Tuple[int, int], pywraplp.Variable], dict[int, pywraplp.Variable]]:
        """ Create the gurobi model for the pricing problem. Formulation adapted
        from https://how-to.aimms.com/Articles/332/332-Formulation-CVRP.html
        and https://how-to.aimms.com/Articles/332/332-Time-Windows.html. Since this
        model generates a single route, indexing over all trucks and requiring
        that all customers are visited are excepted.
        :return: sub_mdl, x, and s, which are respectively the gurobi model, a
        dictionary of variables representing arcs traveled, and a dictionary
        of variables representing arrival times at each customer
        """
        # make model
        sub_model = pywraplp.Solver.CreateSolver('CBC')

        # force early termination of pricing problem, so we can solve it repeatedly
        # in fixed time period. tweak these parameters to find the right trade-off
        # between quantity and quality of columns generated
        sub_model_params = pywraplp.MPSolverParameters()
        sub_model_params.SetDoubleParam(sub_model_params.RELATIVE_MIP_GAP, self.parameters['pricing_problem_mip_gap'])

        # create variables
        # x_i_j if this route travels from node i to node j
        x = {(i, j): sub_model.BoolVar(name=f'x_{i}_{j}')
             for i in self.dat.nodes for j in self.dat.nodes if i != j}
        # s_i time when service begins at node i
        s = {i: sub_model.NumVar(lb=f['open'], ub=f['close']-f['service_time'], name=f's_{i}')
             for i, f in self.dat.nodes.items()}

        # set constraints
        # 9) Any node j entered by this route must be left
        for j in self.dat.nodes:
            sub_model.Add(
                sub_model.Sum([x[i, j] for i in self.dat.nodes if i != j]) -
                sub_model.Sum([x[j, i] for i in self.dat.nodes if j != i]) == 0,
                name=f"flow_conserve_{j}")
        # 10) The route leaves the depot at most once
        sub_model.Add(
            sub_model.Sum([x[self.depot_idx, j] for j in self.dat.orders]) <= 1,
            name=f"include_depot")
        # 11) Route stays within capacity
        sub_model.Add(
            sub_model.Sum([sub_model.Sum([f['weight'] * x[i, j] for j, f in self.dat.orders.items()
                                    if i != j]) for i in self.dat.nodes])
            <= self.parameters['truck_capacity'], name=f"capacity")

        # 12) If route serves customers/orders i then j, the latter must occur
        # after the travel time from the former
        for i in self.dat.nodes:
            for j in self.dat.orders:
                if i == j:
                    continue
                sub_model.Add(
                    s[i] + self.dat.nodes[i]['service_time'] + self.dat.arcs[i, j]['travel_time'] -
                    self.M * (1 - x[i, j]) <= s[j], f'travel_time_{i}_{j}')

        return sub_model, sub_model_params, x, s

    def _time_since_start(self):
        return time.time() - self.time_start

    def solve(self) -> Union[None, dict[str, dict[str, Any]]]:
        """ Find a good solution to VRP using column generation and set covering.
        Uses most of the allotted solve time to iterate between solving the master
        and pricing problem to generate routes. Uses the remaining time to solve
        the master problem with binary variables to generate a collection of
        demand covering routes.
        :return: None
        """
        remaining_solve_time = self.parameters['max_solve_time'] - self.init_time
        # set covering is not the hardest mip to solve, so give most of the time to column generation
        col_gen_end = self._time_since_start() + self.parameters["column_generation_solve_ratio"] * \
            remaining_solve_time
        finding_better_routes = True
        find_all_routes = False  # todo, cleanup this

        # iterate between solving master and column_generation to generate routes
        # until we don't find improving routes or we run out of time
        prev_model_obj_value = float('inf')
        model_mip_gap = float('inf')
        count = 0
        count_no_improvement = 0
        while (finding_better_routes or find_all_routes) and self._time_since_start() < col_gen_end and \
                model_mip_gap > self.parameters['master_problem_mip_gap']:
            if count > 0:
                self.model, self.z, self.c, self.routes, self.route_costs = self._create_master_problem(solver_id='GLOP')
            model_obj = self.model.Sum([self.route_costs[route_idx] * self.z[route_idx] for route_idx in self.z.keys()])
            self.model.Minimize(model_obj)
            model_status = self.model.Solve()
            if model_status != 0:
                pywraplp.Solver.INFEASIBLE == 2
                pywraplp.Solver.ABNORMAL == 4  # means trivially invalid
                assert False

            if model_status == 0 and self.model.Objective().Value() > \
                    (1 - self.parameters['min_column_generation_progress']) * prev_model_obj_value:
                count_no_improvement += 1
                if count_no_improvement == self.max_count_no_improvements:
                    print(f'We move on, since we are not making reasonable progress for {count_no_improvement} iterations')
                    print('count', count)
                    print('prev_model_obj_value', prev_model_obj_value)
                    print('model_obj_value', self.model.Objective().Value())
                    print('min_column_generation_progress', self.parameters['min_column_generation_progress'])
                    break
            elif model_status != 0:
                print(f'We move on, since model_status is: {model_status}')
                print('count', count)
                print('prev_model_obj_value', prev_model_obj_value)
                print('model_obj_value', self.model.Objective().Value())
                print('min_column_generation_progress', self.parameters['min_column_generation_progress'])
            else:
                count_no_improvement = 0
            if model_status == 0:
                prev_model_obj_value = self.model.Objective().Value()
            # reduced cost of a column = (column objective coefficient) - (row duals)^n_nurse_types * column coefs
            obj = self.sub_model.Sum([f['cost'] * self.x[i, j] for (i, j), f in self.dat.arcs.items() if (i,j)!=(0,0)]) - \
                  self.sub_model.Sum([self.c[j].dual_value() * self.sub_model.Sum([self.x[i, j] for i in self.dat.nodes if i != j])
                               for j in self.dat.orders])
            self.sub_model.Minimize(obj)

            t0 = time.time()

            # todo, move this, maybe solve twice
            self.sub_model.SetTimeLimit(1000 * self.parameters['pricing_problem_time_limit'])
            sub_model_status = self.sub_model.Solve(self.sub_model_params)

            print(f'Time in sub_model solve: {time.time() - t0} on count {count}')
            if sub_model_status != 0:
                print(f'sub_model does not find solutions at count {count}!')
                break
            # if negative objective, we have at least one column with a reduced cost
            if self.sub_model.Objective().Value() < 0:
                self._add_best_routes()
            else:
                finding_better_routes = False
            count += 1

        # update all route variables to binary and resolve to find a good set of covering routes
        # CBC is COIN-OR free MIP solver preinstalled with OR-Tools
        self.model, self.z, self.c, self.routes, self.route_costs = \
            self._create_master_problem(solver_id=self.mip_solver)
        self.model.SetTimeLimit(int(1000 * .1*remaining_solve_time))
        model_obj = self.model.Sum([self.route_costs[route_idx] * self.z[route_idx] for route_idx in self.z.keys()])
        self.model.Minimize(model_obj)
        self.final_model_status = self.model.Solve()

        return self._save_solution()

    def _add_best_routes(self) -> None:
        """ Add to the master problem the best routes found by the pricing problem
        and save their stop orders and arrival times in the route dictionary
        NOTE, we currently only add the best route found with OrTools
        :return: None
        """

        route_idx = len(self.z)
        solution_number = 0
        sub_model_sol_count = 1

        # iterate through columns with reduced costs (for now this is just 1 column)
        while solution_number < sub_model_sol_count:
            route = self._recover_route()
            # for each customer visited, get its corresponding constraint from the
            # master (set covering) problem


            self.route_costs[route_idx] = sum(f['cost'] * self.x[i, j].solution_value() for (i, j), f in self.dat.arcs.items())
            # set constraints
            # 8) each customer must be visited by a route (i.e. have delivery demand met)

            # record the order of its stops, so we can report them later if chosen
            self.routes[route_idx] = route

            route_idx += 1
            solution_number += 1

    def _recover_route(self):
        """ Unpack a route that the pricing problem generated
        :return: route, a dictionary that maps stop order to customer locations
        and arrival times
        """
        route = {0: {'node_idx': self.depot_idx, 'arrival': 0}}
        stop = 1
        node_idx = self._next_stop(self.depot_idx)
        while node_idx != self.depot_idx:
            route[stop] = {'node_idx': node_idx, 'arrival': self.s[node_idx].solution_value()}
            stop += 1
            node_idx = self._next_stop(node_idx)
        route[stop] = {'node_idx': self.depot_idx, 'arrival': self.dat.nodes[self.depot_idx]['close']}
        return route

    def _next_stop(self, current_node_idx) -> int:
        """ Determine the index of the location visited directly after visiting
        location <current_node_idx>, as determined by this solution of the pricing
        problem
        :param current_node_idx: index of the current location in this route
        :return: the index of the next location traveled to in this route
        """
        next_stops = [j for j in self.dat.nodes if current_node_idx != j and
                      self.x[current_node_idx, j].solution_value() > .9]
        if len(next_stops) == 0:
            print('Something is off')
            print([self.x[current_node_idx,j].solution_value() for j in self.dat.nodes if current_node_idx != j])
        return next_stops.pop()

    def _save_solution(self) -> Union[None, dict[str, dict[str, Any]]]:
        """ Save the heuristic solution generated for the exact VRP. Record
        summary statistics and each route's details.
        :return: Optionally, a dictionary of the solution data
        """
        sln = solution_schema.TicDat()
        selected_routes = [k for k, var in self.z.items() if var.solution_value() > .9]

        # record summary stats
        sln.summary['cost'] = self.model.Objective().Value()
        sln.summary['routes'] = len(selected_routes)

        # record the route that each used truck takes
        for k in selected_routes:
            for stop, f in self.routes[k].items():
                sln.routes[k, stop] = f

        # save the solution
        if self.solution_path:
            solution_schema.csv.write_directory(sln, self.solution_path, allow_overwrite=True)
        return make_json_dict(solution_schema, sln, verbose=True)


if __name__ == '__main__':
    project_path = os.getcwd() + '\\pyVrp'  # assumes you are one step out of project folder
    solution_path = project_path + '\\results\\solution.csv'

    instances = ['R101', 'R102', 'C101', 'C102', 'RC1', 'RC2']
    # parameters
    mip_solver = 'CBC'  # SCIP, CBC
    instance_name = 'R101'
    max_solve_time = 10  # 10 * 60

    max_count_no_improvements = 100
    parameters = {'max_solve_time': {'value': max_solve_time},
                  'pricing_problem_mip_gap': {'value': 0.1},  # only works for SCIP, so no effect for CBC
                  'pricing_problem_time_limit': {'value': 180},}
    # Remember to change these paths to match your own
    instance = Instance(project_path + f'\\instances\\Solomon\\{instance_name}.txt', parameters)
    #instance = Instance(project_path + '\\instances\\toy.txt', parameters)

    initial_solution_type, input_dict = 'tw_compatibility_a_la_niko', instance.input_dict
    #initial_solution_type, input_dict = 'singleton', toy_input
    #initial_solution_type, input_dict = 'tw_compatibility_a_la_niko', toy_input

    heuristic_vrp = HeuristicVRP(input_dict=input_dict, solution_dict=True, solution_path=solution_path,
                                 initial_solution_type=initial_solution_type, mip_solver=mip_solver,
                                 max_count_no_improvements=max_count_no_improvements)
    heuristic_sln = heuristic_vrp.solve()

    solver = heuristic_vrp.model
    nodes, arcs, orders = heuristic_vrp.dat.nodes, heuristic_vrp.dat.arcs, heuristic_vrp.dat.orders
    routes, route_costs = heuristic_vrp.routes, heuristic_vrp.route_costs
    tw_compability = heuristic_vrp.tw_compability
    if heuristic_vrp.final_model_status == pywraplp.Solver.OPTIMAL:
        print()
        print('Heuristic Solution:')
        print('-------------------')
        routes_without_depot = heuristic_vrp._print_routes(heuristic_vrp.routes)
        for route_without_depot in routes_without_depot:
            assert route_is_feasible(route_without_depot, nodes, arcs, orders, instance.truck_capacity), \
                f'Something is off, we have an infeasible route: {route_without_depot}'
        print('z values:')
        [print(f'z_{route_idx} = {value.solution_value()}') for route_idx, value in heuristic_vrp.z.items()]
        print('Objective value =', solver.Objective().Value())
    else:
        print('The problem does not have an optimal solution.')
    print(f'Instance name: {instance_name}')
