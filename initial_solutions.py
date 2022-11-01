import numpy as np
from pyVrp.helpers import route_is_feasible_by_time, get_temp_route, route_is_feasible


def initial_solution(nodes, arcs, orders, fleet_size, max_truck_capacity):
    """This function is heavily inspired of the article from this webpage:
        https://www.witpress.com/Secure/elibrary/papers/UT04/UT04022FU.pdf
        Note, routes in this function are without edges from and to depot (0)"""
    n = len(nodes)
    tw_compatibility = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                tw_compatibility[i, j] = -1
            else:  # assume now i -> j
                l_j = nodes[j]['close'] - nodes[j]['service_time']
                e_j = nodes[j]['open']
                ae_j = nodes[i]['open'] + nodes[i]['service_time'] + arcs[(i, j)]['travel_time']
                al_j = nodes[j]['close'] + arcs[(i, j)]['travel_time']
                if l_j - ae_j > 0:
                    value = min(l_j, al_j) - max(e_j, ae_j)
                else:
                    value = -float('inf')
                tw_compatibility[i, j] = value
    big_val = tw_compatibility.max() * 100
    seed_values = []
    for i in range(n):
        seed_value = 0
        for j in range(n):
            if i == j:
                continue
            else:
                tw_ij = tw_compatibility[i, j] if tw_compatibility[i, j] != -float('inf') else -big_val
                tw_ji = tw_compatibility[j, i] if tw_compatibility[j, i] != -float('inf') else -big_val
                seed_value += 2 * tw_ij + 1 * tw_ji  # we choose to weigh higher option to get out of the node.
        seed_values.append(seed_value)
    sorted_customers = np.argsort(seed_values)
    seed_customers = sorted_customers[:fleet_size]  # assumes fleet_size <= customers, which is fair!
    seed_truck_capacity = [orders[seed_customer]['weight'] for seed_customer in seed_customers]
    not_placed_customers = sorted_customers[fleet_size:]
    if 0 in seed_customers:
        seed_customers = seed_customers[seed_customers > 0]
    if 0 in not_placed_customers:
        not_placed_customers = not_placed_customers[not_placed_customers > 0]
    routes = {i: [seed_customer] for i, seed_customer in enumerate(seed_customers)}

    def _better_route_and_position(route_value_, customer_index_, route_, best_route_value_, best_customer_index_,
                                   best_route_index_):
        if route_value_ < best_route_value_:
            best_route_value_ = route_value_
            best_customer_index_ = customer_index_
            best_route_index_ = route_
        return best_route_value_, best_customer_index_, best_route_index_

    for count, customer in enumerate(not_placed_customers):
        best_route_index = -1
        best_customer_index = -1
        best_route_value = 9999999
        for route_idx, route in routes.items():
            if orders[customer]['weight'] + seed_truck_capacity[route_idx] <= max_truck_capacity:
                for customer_index, customer_on_route in enumerate(route):
                    temp_route = get_temp_route(route, customer_index, customer)
                    if customer_index == 0:
                        # Note, for now 'cost' and 'time' are the same for routes
                        route_value = arcs[0, customer]['cost'] + nodes[customer]['service_time'] \
                        + arcs[customer, customer_on_route]['cost'] - arcs[0, customer_on_route]['cost']
                        if -float('inf') != tw_compatibility[customer, customer_on_route] \
                                and route_is_feasible_by_time(temp_route, nodes, arcs):
                            best_route_value, best_customer_index, best_route_index = \
                                _better_route_and_position(route_value, customer_index, route_idx, best_route_value,
                                                           best_customer_index, best_route_index)
                    elif 0 < customer_index < len(route) - 1:
                        customer_before_on_route = route[customer_index-1]
                        route_value = arcs[customer_before_on_route, customer]['cost'] \
                                      + arcs[customer, customer_on_route]['cost'] \
                                      - arcs[customer_before_on_route, customer_on_route]['cost'] \
                                      + nodes[customer]['service_time']
                        if -float('inf') != (tw_compatibility[customer_before_on_route, customer] +
                                             tw_compatibility[customer, customer_on_route]) \
                                and route_is_feasible_by_time(temp_route, nodes, arcs):
                            best_route_value, best_customer_index, best_route_index = \
                                _better_route_and_position(route_value, customer_index, route_idx, best_route_value, best_customer_index,
                                                          best_route_index)
                    if customer_index == len(route) - 1:
                        customer_index_last = customer_index + 1
                        temp_route = get_temp_route(route, customer_index_last, customer)
                        route_value = arcs[customer_on_route, customer]['cost'] + nodes[customer]['service_time']
                        if -float('inf') != tw_compatibility[customer_on_route, customer] \
                                and route_is_feasible_by_time(temp_route, nodes, arcs):
                            best_route_value, best_customer_index, best_route_index = \
                                _better_route_and_position(route_value, customer_index_last, route_idx, best_route_value, best_customer_index,
                                                          best_route_index)
        assert best_route_index != -1, f'we cannot place customer {customer}'
        routes[best_route_index].insert(best_customer_index, customer)

    # try to attach routes to each together in the ends before we're done
    routes_combined = []
    route_combinations = []
    for i, route_i in routes.items():
        for j, route_j in routes.items():
            if i!=j and i not in routes_combined and j not in routes_combined:
                if tw_compatibility[route_i[-1], route_j[0]] != float('inf') \
                        and route_is_feasible(route_i + route_j, nodes, arcs, orders, max_truck_capacity):
                    route_combinations.append((i,j))
                    routes_combined.append(i)
                    routes_combined.append(j)
                elif tw_compatibility[route_j[-1], route_i[0]] != float('inf') \
                        and route_is_feasible(route_j + route_i, nodes, arcs, orders, max_truck_capacity):
                    route_combinations.append((j, i))
                    routes_combined.append(i)
                    routes_combined.append(j)
    route_idx = len(routes)
    for (i,j) in route_combinations:
        pass
        new_route = routes[i] + routes[j]
        routes[route_idx] = new_route
        route_idx += 1
        del routes[i]
        del routes[j]
    routes_ = dict()
    for i, (_, route) in enumerate(routes.items()):
        routes_[i] = route

    return routes_, tw_compatibility
