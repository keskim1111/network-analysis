from collections import defaultdict
from pprint import pprint

import gurobipy as gp
from gurobipy import GRB
from helpers import timeit, timeout
import logging
import networkx as nx


class Newman_ILP_RODED:
    def __init__(self, G, weight=None, IntFeasTol=0, TimeLimit=0):
        """
        :param G: networkx graph
        :param nodes:
        """
        self.nodes_list = list(G.nodes)
        self.num_of_nodes = len(self.nodes_list)
        self.G = G
        self.weight = weight
        self.model = gp.Model("mip1")
        # params
        if IntFeasTol > 0:
            self.model.setParam("IntFeasTol", IntFeasTol)
        if TimeLimit > 0:
            self.model.setParam("TimeLimit", TimeLimit)
        self.run()  # setting objective function and constraints and optimizing
        self.communities = self.get_communities()

    def run(self):
        self.set_objective()
        self.add_constraints()
        print("starting to optimize")
        self.model.optimize()


    """
    Objective Function: [sum_ij](q_ij * (y_ij +  1 - z_ijj))
    while: q_ij = a_ij - (d_i * d_j)/2m
        y_ij <=x_i
        y_ij <=x_j
        y_ij >=x_i + x_j -1 
        z_ij == x_i + x_j - y_ijj
    """
    @timeit
    def set_objective(self):
        m = self.G.size(weight=self.weight)
        adj = self.G.adj
        objective_function = 0
        for node_range_1 in range(self.num_of_nodes):
            i = self.nodes_list[node_range_1]
            globals()[f'x_{i}'] = self.model.addVar(vtype=GRB.BINARY, name=f'x_{i}')
            for node_range_2 in range(node_range_1):  # i < j
                j = self.nodes_list[node_range_2]
                if dict(adj[i].items()).get(j) is not None:
                    a_ij = dict(adj[i].items())[j].get("weight", 1)
                else:
                    a_ij = 0

                globals()[f'y_{i}_{j}'] = self.model.addVar(vtype=GRB.BINARY, name=f'y_{i}_{j}')
                globals()[f'z_{i}_{j}'] = self.model.addVar(vtype=GRB.BINARY, name=f'z_{i}_{j}')

                q_ij = a_ij - (self.G.degree(i, weight=self.weight) * self.G.degree(j, weight=self.weight)) / (2 * m)

                objective_function += (q_ij * (globals()[f'y_{i}_{j}'] + 1 - globals()[f'z_{i}_{j}']))

        self.model.setObjective(objective_function, GRB.MAXIMIZE)

    @timeit
    def add_constraints(self):
        # Assumption: this function is called after set_objective() - which creates the variables
        for node_range_1 in range(self.num_of_nodes):
            for node_range_2 in range(node_range_1):  # j < i
                i = self.nodes_list[node_range_1]
                j = self.nodes_list[node_range_2]

                self.model.addConstr(
                    globals()[f'y_{i}_{j}'] <= globals()[f'x_{i}'])
                self.model.addConstr(
                    globals()[f'y_{i}_{j}'] <= globals()[f'x_{j}'])
                self.model.addConstr(
                    globals()[f'y_{i}_{j}'] >=  globals()[f'x_{i}'] + globals()[f'x_{j}'] -1 )
                self.model.addConstr(
                    globals()[f'z_{i}_{j}'] ==  globals()[f'x_{i}'] + globals()[f'x_{j}'] -globals()[f'y_{i}_{j}'] )



        logging.info("finished adding constraints")

    def get_communities(self):
        communities = defaultdict(set)
        for v in self.model.getVars():
            # print(v)

            if v.VarName.startswith("x"):
                x, node = v.VarName.split("_")
                communities[str(abs(v.X))].add(int(node))
        # pprint(communities)
        com_sets = communities.values()
        if len(com_sets) > 1:
            return list([list(v) for v in communities.values()])
        return list(com_sets)
