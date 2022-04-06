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
from input_networks import create_graph_from_edge_list, create_random_network
from helpers import timeit, adjacency_matrix

msg = "The modularity result of the Algorithm is: "

"""
Assumption: the graph nodes are continous from 0 to num_nodes-1
"""


class ILP:
    def __init__(self, graph_input, is_networx_graph=False, is_edges_file=False):
        print("here")
        if is_edges_file:
            self.graph = create_graph_from_edge_list(graph_input)  # creates networkX graph from edges_file
        if is_networx_graph:
            self.graph = graph_input  # networkX graph
        self.num_of_nodes = self.graph.number_of_nodes()
        self.model = gp.Model("mip1")
        self.set_objective()  # Sets objective function
        self.add_constraints()
        self.model.optimize()
        self.communities = self.find_communities()

    # TODO: add input of mapping and then change node1, node2 according to mapping
    def find_communities(self):
        communities_per_node = {i: [i] for i in range(self.graph.nodes_range)}  # i:com - com is the full community that node i is part of
        node_is_done_list = [0]*self.graph.nodes_range  # 0 if node not in community from the communities list yet
        communities = []

        for v in self.model.getVars():
            node1 = int(v.VarName.split("_")[1])
            node2 = int(v.VarName.split("_")[2])
            if not int(abs(v.X)):  # if in same community
                communities_per_node[node1].append(node2)
                communities_per_node[node2].append(node1)

        # adding community list to communities
        for node, node_community in communities_per_node.items():
            if not node_is_done_list[node]:
                communities.append(node_community)
                for i in node_community:
                    node_is_done_list[i] = 1

        return communities

    """
    objective_function: 1/m * [sum_ij](q_ij * (1 - x_ij))
    while: q_ij = a_ij - (d_i * d_j)/2m
    """

    @timeit
    def set_objective(self):
        G = self.graph
        m = G.number_of_edges()
        total_sum = 0
        adj_matrix = adjacency_matrix(G)
        for j in range(self.num_of_nodes):
            for i in range(j):  # i < j
                q_ij = adj_matrix[i][j] - (G.degree(i) * G.degree(j)) / (2 * m)
                globals()[f'x_{i}_{j}'] = self.model.addVar(vtype=GRB.BINARY, name=f'x_{i}_{j}')
                total_sum += (q_ij * (1 - globals()[f'x_{i}_{j}']))

        objective_function = 1 / m * total_sum
        self.model.setObjective(objective_function, GRB.MAXIMIZE)

    # Assumption: this function is called after set_objective() - which creates the variables
    """
    x_ij + x_jk - x_ik >= 0
    x_ij - x_jk + x_ik >= 0
    -x_ij +x_jk + x_ik >= 0
    """

    @timeit
    def add_constraints(self):
        for k in range(self.num_of_nodes):
            for j in range(k):  # j < k
                for i in range(j):  # i < j
                    self.model.addConstr(
                        globals()[f'x_{i}_{j}'] + globals()[f'x_{j}_{k}'] - globals()[f'x_{i}_{k}'] >= 0)
                    self.model.addConstr(
                        globals()[f'x_{i}_{j}'] - globals()[f'x_{j}_{k}'] + globals()[f'x_{i}_{k}'] >= 0)
                    self.model.addConstr(
                        -globals()[f'x_{i}_{j}'] + globals()[f'x_{j}_{k}'] + globals()[f'x_{i}_{k}'] >= 0)
        for c in self.model.getConstrs():
            print(c.ConstrName, c.Slack)


def trivial_run():
    edges_file = "cliqs_2"
    ilp_obj = ILP(edges_file, is_edges_file=True)
    print(ilp_obj.model.display())
    for v in ilp_obj.model.getVars():
        print('%s %g ' % (v.VarName, v.X))
    # for c in ilp_obj.model.getConstrs():
    #     print(c.ConstrName, c.Slack)
    print('Obj: %g ' % ilp_obj.model.ObjVal)
    print(f'nodes_range: {ilp_obj.num_of_nodes}')
    print(ilp_obj.communities)


@timeit
def run_ilp_on_nx_graph(G):
    ilp_obj = ILP(G, is_networx_graph=True)
    print(ilp_obj.model.display())
    for v in ilp_obj.model.getVars():
        print('%s %g ' % (v.VarName, v.X))
    print('Obj: %g ' % ilp_obj.model.ObjVal)
    print(f'nodes_range: {ilp_obj.num_of_nodes}')
    print(ilp_obj.communities)


# TODO: speak to kim about results + try to implement the algorithm we learnt with shani - and ask shani qs if it
#  doesnt work!

if __name__ == '__main__':
    # trivial_run()
    n = 100
    mu = 0.1
    tau1 = 3
    tau2 = 1.5
    average_degree = 2
    min_com = 5
    G = create_random_network(n, mu, tau1, tau2, average_degree, min_com)
    print(G)
    run_ilp_on_nx_graph(G)
    pass
