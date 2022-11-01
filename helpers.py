from ticdat import TicDatFactory
from copy import copy


parameters = {'master_problem_mip_gap': {'value': .01},
              'solutions_per_pricing_problem': {'value': 'number_customers'},
              'pricing_problem_mip_gap': {'value': .1},
              'pricing_problem_time_limit': {'value': 1},
              'min_column_generation_progress': {'value': .001},
              'column_generation_solve_ratio': {'value': .9}}


# ----------------- Define Input and Output Data Requirements ------------------
# label column headers and set primary key constraints
input_schema = TicDatFactory(
    arcs=[['start_idx', 'end_idx'], ['travel_time', 'cost']],
    nodes=[['idx'], ['name', 'type', 'lat', 'long', 'open', 'close', 'service_time']],
    orders=[['node_idx'], ['weight']],
    parameters=[['key'], ['value']]  # truck capacity
)

# set type constraints (pks default to strings. other cols default to floats)
day_in_seconds = 24 * 60 * 60
input_schema.set_data_type('arcs', 'start_idx', must_be_int=True)
input_schema.set_data_type('arcs', 'end_idx', must_be_int=True)
input_schema.set_data_type('nodes', 'idx', must_be_int=True)
input_schema.set_data_type('nodes', 'name', number_allowed=False, strings_allowed="*", nullable=True)
input_schema.set_data_type('nodes', 'type', number_allowed=False, strings_allowed=('depot', 'customer'))
input_schema.set_data_type('nodes', 'lat', number_allowed=True)  #min=-90, max=90, inclusive_max=True)
input_schema.set_data_type('nodes', 'long',  number_allowed=True)  # min=-180, max=180, inclusive_max=True)
input_schema.set_data_type('nodes', 'open', max=day_in_seconds, inclusive_max=True)
input_schema.set_data_type('nodes', 'close', max=day_in_seconds, inclusive_max=True)
input_schema.set_data_type('nodes', 'service_time', max=day_in_seconds, inclusive_max=True)
input_schema.set_data_type('orders', 'node_idx', must_be_int=True)

# set foreign key constraints (all node indices must be an index of the node table)
input_schema.add_foreign_key('arcs', 'nodes', ['start_idx', 'idx'])
input_schema.add_foreign_key('arcs', 'nodes', ['end_idx', 'idx'])
input_schema.add_foreign_key('orders', 'nodes', ['node_idx', 'idx'])

# set check constraints (all locations close no earlier than they open)
input_schema.add_data_row_predicate('nodes', predicate_name="open_close_check",
    predicate=lambda row: row['open'] + row['service_time'] <= row['close'])

# set parameter constraints
input_schema.add_parameter("truck_capacity", 40000)
input_schema.add_parameter("master_problem_mip_gap", 0.1)
input_schema.add_parameter("fleet_size", 3000)
input_schema.add_parameter("max_solve_time", 60)
input_schema.add_parameter("solutions_per_pricing_problem", "number_customers",
                           strings_allowed=("number_customers",))
input_schema.add_parameter("pricing_problem_mip_gap", .1, max=1)
input_schema.add_parameter("pricing_problem_time_limit", 1)
input_schema.add_parameter("min_column_generation_progress", .001, max=1)
input_schema.add_parameter("column_generation_solve_ratio", .9, max=1)

# solution tables
solution_schema = TicDatFactory(
    summary=[['key'], ['value']],  # routes and cost
    routes=[['idx', 'stop'], ['node_idx', 'arrival']]
)

solution_schema.set_data_type('routes', 'idx', must_be_int=True)
solution_schema.set_data_type('routes', 'stop', must_be_int=True)


# --------------- Define Static Input Data Set for Example Run -----------------
toy_input = {
    'arcs': {
        (0, 1): {'travel_time': 2.3639163739810654, 'cost': 618.1958186990532},
        (1, 0): {'travel_time': 2.3639163739810654, 'cost': 118.19581869905328},
        (0, 2): {'travel_time': 1.5544182164530995, 'cost': 577.720910822655},
        (2, 0): {'travel_time': 1.5544182164530995, 'cost': 77.72091082265497},
        (1, 2): {'travel_time': 0.853048419193608, 'cost': 42.6524209596804},
        (2, 1): {'travel_time': 0.853048419193608, 'cost': 42.6524209596804}
    },
    'nodes': {
        0: {'name': 'depot', 'type': 'depot', 'lat': 39.91, 'long': -76.5, 'open': 0, 'close': 24, 'service_time': 0},
        1: {'name': 'customer 1', 'type': 'customer', 'lat': 39.91, 'long': -74.61, 'open': 13, 'close': 21, 'service_time': 0},
        2: {'name': 'customer 2', 'type': 'customer', 'lat': 39.78, 'long': -75.27, 'open': 7, 'close': 15, 'service_time': 0}
    },
    'orders': {
        1: {'weight': 13084},
        2: {'weight': 8078}
    },
    'parameters': {
        'truck_capacity': {'value': 40000},
        'fleet_size': {'value': 2},
        'max_solve_time': {'value': 60},
    } | parameters
}


def get_temp_route(route, customer_index, customer):
    temp_route = copy(route)
    temp_route.insert(customer_index, customer)
    return temp_route


def route_is_feasible_by_time(route, nodes, arcs):
    """Note route_ is without depot, for example [3,2,5] or [2,1]"""
    route_with_depot = get_temp_route(route, len(route), 0)  # add zero as last customer
    route_feasible = True
    earliest_finish_time = 0
    last_customer = 0
    for i, customer in enumerate(route_with_depot):
        earliest_finish_time = max(earliest_finish_time + arcs[(last_customer, customer)]['travel_time'],
                                   nodes[customer]['open']) \
                               + nodes[customer]['service_time']
        if earliest_finish_time > nodes[customer]['close']:
            route_feasible = False
        last_customer = customer

    return route_feasible


def route_is_feasible(route, nodes, arcs, orders, max_truck_capacity):
    """Note route_ is without depot, for example [3,2,5] or [2,1]"""
    route_with_depot = get_temp_route(route, len(route), 0)  # add zero as last customer
    route_feasible = True
    earliest_finish_time = 0
    last_customer = 0
    weight = 0
    for i, customer in enumerate(route_with_depot):
        earliest_finish_time = max(earliest_finish_time + arcs[(last_customer, customer)]['travel_time'],
                                   nodes[customer]['open']) \
                               + nodes[customer]['service_time']
        if earliest_finish_time > nodes[customer]['close']:
            route_feasible = False
        last_customer = customer
        if customer > 0:
            weight += orders[customer]['weight']
    if weight > max_truck_capacity:
        route_feasible = False

    return route_feasible
