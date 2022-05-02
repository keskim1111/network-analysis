"""
I am using the following article - Discovering Communities in Networks: A Linear
Programming Approach Using Max-Min Modularity.
There is a similar article with more citings - Modularity-maximizing graph communities
via mathematical programming.
- the difference between the articles:
    the objective function in the second divides by 2. (1/2m)
"""
# TODO: make sure I can deal with inner edges


import gurobipy as gp
from gurobipy import GRB
from input_networks import create_graph_from_edge_file, create_random_network, create_graph_from_edge_list
from helpers import timeit, timeout, create_sub_graphs_from_communities
import networkx as nx
import os, pickle
from binary_files import read_binary_network_output


msg = "The modularity result of the Algorithm is: "

"""
Assumption: the graph nodes are continous from 0 to num_nodes-1
# NEW: i changed the code - in a way that the nodes do NOT have to be continuous.
"""


@timeout(120)
class ILP:
    def __init__(self, graph_input, is_networkx_graph=False, is_edges_file=False):
        if is_edges_file:
            self.graph = create_graph_from_edge_file(graph_input)  # creates networkX graph from edges_file
        if is_networkx_graph:
            self.graph = graph_input  # networkX graph
        self.num_of_nodes = self.graph.number_of_nodes()
        self.nodes_list = list(self.graph.nodes())
        self.model = gp.Model("mip1")
        self.set_objective()  # Sets objective function
        self.add_constraints()
        print("starting to optimize")
        self.model.optimize()
        self.communities = self.find_communities()

    def find_communities(self):
        communities_per_node = {i: [i] for i in self.nodes_list}  # i:com - com is the full community that node i is part of
        node_is_done_dict = {i: 0 for i in self.nodes_list}  # 0 if node not in community from the communities list yet

        communities = []

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

    """
    objective_function: 1/m * [sum_ij](q_ij * (1 - x_ij))
    while: q_ij = a_ij - (d_i * d_j)/2m
    """

    def set_objective(self):
        G = self.graph
        m = G.number_of_edges()
        total_sum = 0
        adj_dict = G.adj # Assumption: G.adj is 2 sided (if ij are neighbors then so is ji)
        for node_range_1 in range(self.num_of_nodes):
            for node_range_2 in range(node_range_1):  # i < j
                j = self.nodes_list[node_range_1]
                i = self.nodes_list[node_range_2]
                if_ij_edge = 1 if dict(adj_dict[i].items()).get(j) is not None else 0
                #if_ij_edge = 1 if adj_dict[i].items().get(j, 0) else 0
                #if_ij_edge = 1 if adj_dict[i].get({j:{}}, 0) else 0
                q_ij = if_ij_edge - (G.degree(i) * G.degree(j)) / (2 * m)
                globals()[f'x_{i}_{j}'] = self.model.addVar(vtype=GRB.BINARY, name=f'x_{i}_{j}')
                total_sum += (q_ij * (1 - globals()[f'x_{i}_{j}']))

        objective_function = 1 / m * total_sum
        self.model.setObjective(objective_function, GRB.MAXIMIZE)
        print("finished setting objective function")

    # Assumption: this function is called after set_objective() - which creates the variables
    """
    x_ij + x_jk - x_ik >= 0
    x_ij - x_jk + x_ik >= 0
    -x_ij +x_jk + x_ik >= 0
    """

    def add_constraints(self):
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


def trivial_run():
    edges_file = "tests/cliqs_2"
    ilp_obj = ILP(edges_file, is_edges_file=True)
    print(ilp_obj.model.display())
    # for v in ilp_obj.model.getVars():
    #     print('%s %g ' % (v.VarName, v.X))
    # for c in ilp_obj.model.getConstrs():
    #     print(c.ConstrName, c.Slack)
    print('Obj: %g ' % ilp_obj.model.ObjVal)
    print(f'nodes_range: {ilp_obj.num_of_nodes}')
    print(ilp_obj.communities)
    return ilp_obj


@timeit
def run_ilp_on_nx_graph(G):
    ilp_obj = ILP(G, is_networkx_graph=True)
    # print(ilp_obj.model.display())
    # for v in ilp_obj.model.getVars():
    #     print('%s %g ' % (v.VarName, v.X))
    print('Obj: %g ' % ilp_obj.model.ObjVal)
    print(f'nodes_range: {ilp_obj.num_of_nodes}')
    print(ilp_obj.communities)
    return ilp_obj


# if __name__ == '__main__':
#     # trivial_run()
#     n = 100
#     mu = 0.1
#     tau1 = 3
#     tau2 = 1.5
#     average_degree = 2
#     min_com = 5
#     G = create_random_network(n, mu, tau1, tau2, average_degree, min_com)
#     real_communities = {frozenset(G.nodes[v]["community"]) for v in G}
#     print(f'real_communities: {real_communities}')
#     real_modularity = nx.algorithms.community.modularity(G, real_communities)
#     print(f'real_modularity: {real_modularity}')
#     ilp_obj = run_ilp_on_nx_graph(G)
#     ilp_modularity = nx.algorithms.community.modularity(G, ilp_obj.communities)
#     print(f'ilp_modularity: {ilp_modularity}')
#
#     pass
