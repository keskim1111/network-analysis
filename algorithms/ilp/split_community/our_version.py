from collections import defaultdict

import gurobipy as gp
from gurobipy import GRB
from utils.helpers import timeit
import logging


class Newman_ILP:
    def __init__(self, G, weight=None, IntFeasTol=None, TimeLimit=None):
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
        if IntFeasTol is not None:
            self.model.setParam("IntFeasTol", IntFeasTol)
        if TimeLimit is not None:
            self.model.setParam("TimeLimit", TimeLimit)
        self.run()  # setting objective function and constraints and optimizing
        self.communities = self.get_communities()

    def run(self):
        self.set_objective()
        self.add_constraints()
        print("starting to optimize")
        self.model.optimize()

    """
    Objective Function: [sum_ij](q_ij * (y_ij + t_ijj))
    while: q_ij = a_ij - (d_i * d_j)/2m
    """

    @timeit
    def set_objective(self):
        m = self.G.size(weight=self.weight)
        adj = self.G.adj
        objective_function = 0
        for node_range_1 in range(self.num_of_nodes):
            i = self.nodes_list[node_range_1]
            globals()[f'x_{i}'] = self.model.addVar(vtype=GRB.BINARY, name=f'x_{i}')
            globals()[f't_{i}'] = self.model.addVar(vtype=GRB.BINARY, name=f't_{i}')
            for node_range_2 in range(node_range_1):  # i < j
                j = self.nodes_list[node_range_2]
                if dict(adj[i].items()).get(j) is not None:
                    a_ij = dict(adj[i].items())[j].get("weight", 1)
                else:
                    a_ij = 0
                q_ij = a_ij - (self.G.degree(i, weight=self.weight) * self.G.degree(j, weight=self.weight)) / (2 * m)

                globals()[f'y_{i}_{j}'] = self.model.addVar(vtype=GRB.BINARY, name=f'1_{i}_{j}')
                globals()[f't_{i}_{j}'] = self.model.addVar(vtype=GRB.BINARY, name=f'0_{i}_{j}')

                objective_function += (q_ij * (globals()[f'y_{i}_{j}'] + globals()[f't_{i}_{j}']))

        self.model.setObjective(objective_function, GRB.MAXIMIZE)

    @timeit
    def add_constraints(self):
        # Assumption: this function is called after set_objective() - which creates the variables
        for node_range_1 in range(self.num_of_nodes):
            for node_range_2 in range(node_range_1):  # j < i
                i = self.nodes_list[node_range_1]
                j = self.nodes_list[node_range_2]

                # y_ij ==1 iff x_j==x_i==1
                self.model.addGenConstrAnd(globals()[f'y_{i}_{j}'], [globals()[f'x_{i}'], globals()[f'x_{j}']],
                                           name="andconstr")
                # t_i ==1 - x_i
                self.model.addConstr(globals()[f't_{i}'] == 1 - globals()[f'x_{i}'])
                # t_j ==1 - x_j
                self.model.addConstr(globals()[f't_{j}'] == 1 - globals()[f'x_{j}'])
                # t_ij ==1 iff x_j==x_i==0
                self.model.addGenConstrAnd(globals()[f't_{i}_{j}'], [globals()[f't_{i}'], globals()[f't_{j}']],
                                           name="andconstr")

        logging.debug("finished adding constraints")

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
