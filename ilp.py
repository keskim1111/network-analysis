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
from Graph import Graph
from datetime import datetime
from input_networks import create_random_network
from algorithms import algorithms_partition_for_colors
import networkx as nx
from output_generator import create_visual_graph


msg = "The modularity result of the Algorithm is: "


class ILP:
    def __init__(self, edges, edges_is_list=False):
        start = datetime.now()
        self.graph = Graph(edges, edges_is_list)
        self.model = gp.Model("mip1")
        self.set_objective()  # Sets objective function
        self.add_constraints()
        self.model.optimize()
        self.communities = self.find_communities()
        end = datetime.now()
        print(f'ILP object took {end-start} seconds')

    def find_communities(self):
        communities_per_node = {}
        counter = 0
        for v in self.model.getVars():
            counter += 1
            node1 = v.VarName.split("_")[1]
            node2 = v.VarName.split("_")[2]
            inSameCommunity = int(abs(v.X))
            if inSameCommunity:
                if node1 not in communities_per_node:
                    communities_per_node[node1] = []
                communities_per_node[node1].append(node2)
                if node2 not in communities_per_node:
                    communities_per_node[node2] = []
                communities_per_node[node2].append(node1)
            else:
                print(f'{node1}, {node2} not in same community')
        print(counter)
        return communities_per_node

    """
    objective_function: 1/m * [sum_ij](q_ij * (1 - x_ij))
    while: q_ij = a_ij - (d_i * d_j)/2m
    """
    def set_objective(self):
        start = datetime.now()
        print(f'function set_objective starting - {start}')
        G = self.graph
        m = len(G.edges_list)
        sum = 0
        for j in range(G.nodes_range):
            for i in range(j):  # i < j
                q_ij = G.adj_matrix[i][j] - (G.degree_list[i] * G.degree_list[j]) / (2*m)
                globals()[f'x_{i}_{j}'] = self.model.addVar(vtype=GRB.BINARY, name=f'x_{i}_{j}')
                sum += (q_ij * (1 - globals()[f'x_{i}_{j}']))

        objective_function = 1/m * (sum)
        #objective_function = sum
        self.model.setObjective(objective_function, GRB.MAXIMIZE)
        end = datetime.now()
        print(f'function set_objective ended and took {end-start} seconds')
    # Assumption: this function is called after set_objective() - which creates the variables
    """
    x_ij + x_jk - x_ik >= 0
    x_ij - x_jk + x_ik >= 0
    -x_ij +x_jk + x_ik >= 0
    """
    def add_constraints(self):
        start = datetime.now()
        print(f'function add_constraints starting - {start}')
        G = self.graph
        for k in range(G.nodes_range):
            for j in range(k):  # j < k
                for i in range(j):  # i < j
                    self.model.addConstr(globals()[f'x_{i}_{j}'] + globals()[f'x_{j}_{k}'] - globals()[f'x_{i}_{k}'] >= 0)
                    self.model.addConstr(globals()[f'x_{i}_{j}'] - globals()[f'x_{j}_{k}'] + globals()[f'x_{i}_{k}'] >= 0)
                    self.model.addConstr(-globals()[f'x_{i}_{j}'] + globals()[f'x_{j}_{k}'] + globals()[f'x_{i}_{k}'] >= 0)
        end = datetime.now()
        print(f'function add_constraints ended and took {end-start} seconds')


ilp_obj = ILP("C:/Users/97252/Documents/year_4/sadna/tests/network_2_cliques.dat")
# G = create_random_network(50, 0.1, 3, 1.5, 2, 5)
# real_communities = {frozenset(G.nodes[v]["community"]) for v in G}
# print(f'real_communities: {real_communities}')
# real_partition = algorithms_partition_for_colors(real_communities)
# print(f"Real - {msg}{nx.algorithms.community.modularity(G, real_communities)} with {len(real_communities)} "
#       f"communities and {sum(len(sett) for sett in real_communities)} items")
# create_visual_graph(G, real_partition, "real")

# edges_list = G.edges
# ilp_obj = ILP(edges_list, edges_is_list=True)

print(ilp_obj.model.display())
for v in ilp_obj.model.getVars():
    print('%s %g ' % (v.VarName, v.X))
# for c in ilp_obj.model.getConstrs():
#     print(c.ConstrName, c.Slack)
print('Obj: %g ' % ilp_obj.model.ObjVal)
print(f'nodes_range: {ilp_obj.graph.nodes_range}')
print(ilp_obj.communities)


# TODO: speak to kim about results + try to implement the algorithm we learnt with shani - and ask shani qs if it doesnt work!
