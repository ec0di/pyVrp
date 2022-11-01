# make sure, we are not finding an already found route.

# if self.routes is not None:
#     for route_idx, route in self.routes.items():
#         routes_list_of_tuple = []
#         for node_idx, node in route.items():
#             if node_idx == 0:
#                 last_node = node
#                 continue
#             else:
#                 routes_list_of_tuple.append((last_node['node_idx'], node['node_idx']))
#                 #len(route) - 1
#                 last_node = node
#         #print('routes_list_of_tuple')
#         #print(routes_list_of_tuple)
#         nodes_in_route = 0
#         nodes_not_in_route = 0
#         for i in self.dat.nodes:
#             for j in self.dat.nodes:
#                 if i != j:
#                     if (i, j) not in routes_list_of_tuple:
#                         nodes_not_in_route += x[(i, j)]
#                         #print('im here')
#                     else:
#                         nodes_in_route += x[(i, j)]
#         y0, y1 = sub_model.BoolVar(f'y0_{route_idx}'), sub_model.BoolVar(f'y1_{route_idx}')
#         #{i: sub_model.NumVar(lb=f['open'], ub=f['close'] - f['service_time'], name=f's_{i}')
#         # for i, f in self.dat.nodes.items()}
#         big_m = 99999
#         sub_model.Add(len(routes_list_of_tuple) - nodes_in_route >= (1-y0) / big_m, f'route_excluded_{route_idx}_c1')
#         sub_model.Add(nodes_not_in_route >= (1-y1) / big_m, f'route_excluded_{route_idx}_c2')
#         sub_model.Add(y0 + y1 <= 1, f'route_excluded_{route_idx}_c3')

# sub_model.Add(nodes_in_route - nodes_not_in_route == len(routes_list_of_tuple), f'route_excluded_{route_idx}_c1')



# todo, make it possible not to recreate z variables, but reuse model in fun _add_best_routes()
#    # add the new route as another possible route to visit customers
# self.z[route_idx] = self.model.NumVar(name=f'z_{route_idx}', ub=0, lb=1)

# for j, cs in self.c.items():
#    cs.SetCoefficient(self.z[route_idx], sum([j in [x['node_idx'] for x in route.values()]]))
#    # we remember to add new z to objective function (done outside this function)


# # todo One could recreate sub_problem for all iterations, but why?!
# self.sub_model, self.sub_model_params, self.x, self.s = self._create_subproblem()
# obj = self.sub_model.Sum(
#    [f['cost'] * self.x[i, j] for (i, j), f in self.dat.arcs.items() if (i, j) != (0, 0)]) - \
#      self.sub_model.Sum(
#          [self.c[j].dual_value() * self.sub_model.Sum([self.x[i, j] for i in self.dat.nodes if i != j])
#           for j in self.dat.orders])
# self.sub_model.Minimize(obj)
# self.sub_model.SetTimeLimit(1000 * self.parameters['pricing_problem_time_limit'])
# sub_model_status = self.sub_model.Solve(self.sub_model_params)
# print('final_sub_model_status:', sub_model_status)


# todo, look into multiple solutions from subproblem
#.AllSolutionCollector()#SolutionCollector()

# todo, maybe parameters for SCIP needs to be specifed as string
# SetSolverSpecificParametersAsString for SCIP
