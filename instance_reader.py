import pandas as pd
import numpy as np
from pyVrp.helpers import parameters as standard_parameters


class Instance:
    def __init__(self, instance_path, parameters):
        """assumption 1: Currently I assume that DueDate is the latest start of the service at the given customer. This
        is due to Solomon 100 customers dataset, which seems to have this assumption.
        assumption 2 (old): I made the code first with the assumption that the service should finish before the DueDate.
        However, the code is easily converted from assumption 2 to assumption 1. What we can and will do is just prolong
        the DueDate with the service time, and problem is solved"""
        df = pd.read_csv(instance_path)
        self.fleet_size = int(df.iloc[2][0].strip(' ').split(' ')[0])
        self.truck_capacity = int(df.iloc[2][0].strip(' ').split(' ')[-1])

        df = pd.read_csv(instance_path, skiprows=7, skip_blank_lines=True, engine='python',
                         delim_whitespace=True).drop(columns=['DUE', 'DATE', 'SERVICE', 'TIME.1'])
        df.columns = ['CustomerNum', 'XCoord', 'YCoord', 'Demand', 'ReadyTime', 'DueDate', 'ServiceTime']
        # VRP problem renaming
        self.instance_df = df
        # notice first row is the depot

        # calc travel times and costs (they are the same for this instance type)
        coords = [(coord.XCoord, coord.YCoord) for coord in df[['XCoord', 'YCoord']].itertuples()]
        z = np.array([[complex(coord[0], coord[1]) for coord in coords]])  # notice the [[ ... ]]
        dists = abs(z.T - z)
        # truncate dists to 1 or 2 decimals.
        dists = np.round(dists, 2)
        self.dists = dists

        # create input_dict
        arcs = dict()
        nodes = dict()
        weights = dict()
        for i_tup in self.instance_df.itertuples():
            for j_tup in self.instance_df.itertuples():
                i, j = i_tup.CustomerNum, j_tup.CustomerNum
                if i == j:
                    continue
                else:
                    arcs[(i, j)] = dict(travel_time=self.dists[i, j], cost=self.dists[i, j])
            if i == 0:
                node = dict(name='depot', type='depot')
            else:
                node = dict(name=f'customer {i}', type='customer')
                weights[i] = dict(weight=i_tup.Demand)
            # Note, notice that we prolong the opening period of customer i with the service time.
            node |= dict(lat=i_tup.XCoord, long=i_tup.YCoord, open=i_tup.ReadyTime, close=i_tup.DueDate + i_tup.ServiceTime,
                         service_time=i_tup.ServiceTime)
            nodes[i] = node

        self.input_dict = {
            'arcs': arcs,
            'nodes': nodes,
            'orders': weights,
            'parameters': {'truck_capacity': {'value': self.truck_capacity},
                           'fleet_size': {'value': self.fleet_size}} | standard_parameters}
        self.input_dict['parameters'].update(parameters)
