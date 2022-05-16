"""
I am using the following article - Discovering Communities in Networks: A Linear
Programming Approach Using Max-Min Modularity.
There is a similar article with more citings - Modularity-maximizing graph communities
via mathematical programming.
- the difference between the articles:
    the objective function in the second divides by 2. (1/2m)
"""
# TODO: make sure I can deal with inner edges

"""
# NEW: i changed the code - in a way that the nodes do NOT have to be continuous.
"""

import gurobipy as gp
from gurobipy import GRB
from input_networks import create_graph_from_edge_file, create_random_network, create_graph_from_edge_list
from helpers import timeit, timeout
import networkx as nx


# @timeout(300) # 5 min
class ILP:
    def __init__(self, G, nodes: list, weight=None, IntFeasTol=float(1e-5), TimeLimit=0):
        """
        :param G: networkx graph
        :param nodes:
        """
        self.nodes_list = nodes
        self.num_of_nodes = len(self.nodes_list)
        self.G = G
        self.weight = weight
        self.model = gp.Model("mip1")
        #params
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
    Objective Function: [sum_ij](q_ij * (1 - x_ij))
    while: q_ij = a_ij - (d_i * d_j)/2m
    """
    @timeit
    def set_objective(self):
        m = self.G.size(weight=self.weight)
        adj = self.G.adj
        objective_function = 0
        for node_range_1 in range(self.num_of_nodes):
            for node_range_2 in range(node_range_1):  # i < j
                j = self.nodes_list[node_range_1]
                i = self.nodes_list[node_range_2]

                if dict(adj[i].items()).get(j) is not None:
                    a_ij = dict(adj[i].items())[j].get("weight", 1)
                else:
                    a_ij = 0

                q_ij = a_ij - (self.G.degree(i) * self.G.degree(j)) / (2 * m)
                globals()[f'x_{i}_{j}'] = self.model.addVar(vtype=GRB.BINARY, name=f'x_{i}_{j}')
                objective_function += (q_ij * (1 - globals()[f'x_{i}_{j}']))

        self.model.setObjective(objective_function, GRB.MAXIMIZE)

    """
    Constraints:
    x_ij + x_jk - x_ik >= 0
    x_ij - x_jk + x_ik >= 0
    -x_ij +x_jk + x_ik >= 0
    """
    @timeit
    def add_constraints(self):
        # Assumption: this function is called after set_objective() - which creates the variables
        for node_range_1 in range(self.num_of_nodes):
            for node_range_2 in range(node_range_1):  # j < k
                for node_range_3 in range(node_range_2):  # i < j
                    k = self.nodes_list[node_range_1]
                    j = self.nodes_list[node_range_2]
                    i = self.nodes_list[node_range_3]
                    self.model.addConstr(
                        globals()[f'x_{i}_{j}'] + globals()[f'x_{j}_{k}'] - globals()[f'x_{i}_{k}'] >= 0)
                    self.model.addConstr(
                        globals()[f'x_{i}_{j}'] - globals()[f'x_{j}_{k}'] + globals()[f'x_{i}_{k}'] >= 0)
                    self.model.addConstr(
                        -globals()[f'x_{i}_{j}'] + globals()[f'x_{j}_{k}'] + globals()[f'x_{i}_{k}'] >= 0)
        print("finished adding constraints")
        # for c in self.model.getConstrs():
        #     print(c.ConstrName, c.Slack)

    def get_communities(self):
        communities = []
        communities_per_node = {i: [i] for i in self.nodes_list}  # i:com - com is the full community that node i is part of
        node_is_done_dict = {i: 0 for i in self.nodes_list}  # 0 if node not in community from the communities list yet

        for v in self.model.getVars():
            node1 = int(v.VarName.split("_")[1])
            node2 = int(v.VarName.split("_")[2])
            if not int(abs(v.X)):  # if in same community
                communities_per_node[node1].append(node2)
                communities_per_node[node2].append(node1)

        # adding community list to communities
        for node, node_community in communities_per_node.items():
            if not node_is_done_dict[node]:
                communities.append(node_community)
                for i in node_community:
                    node_is_done_dict[i] = 1

        return communities
