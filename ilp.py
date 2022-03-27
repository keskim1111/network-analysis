"""
I am using the following article - Discovering Communities in Networks: A Linear
Programming Approach Using Max-Min Modularity.
There is a similar article with more citings - Modularity-maximizing graph communities
via mathematical programming.
- the difference between the articles:
    the objective function in the second divides by 2. (1/2m)
"""

# TODO: try downloading an academic license - or creating a smaller benchmark network (understand the parameters!)
import gurobipy as gp
from gurobipy import GRB
from Graph import Graph
from datetime import datetime


class ILP:
    def __init__(self, graph_file):
        start = datetime.now()
        self.graph = Graph(graph_file, load_pickle=True)
        self.model = gp.Model("mip1")
        self.set_objective()  # Sets objective function
        self.add_constraints()
        self.model.optimize()
        end = datetime.now()
        print(f'ILP object took {end-start} seconds')

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
                globals()[f'x_{i}{j}'] = self.model.addVar(vtype=GRB.BINARY, name=f'x_{i}{j}')
                sum += (q_ij * (1 - globals()[f'x_{i}{j}']))

        objective_function = 1/m * (sum)
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
                    self.model.addConstr(globals()[f'x_{i}{j}'] + globals()[f'x_{j}{k}'] - globals()[f'x_{i}{k}'] >= 0)
                    self.model.addConstr(globals()[f'x_{i}{j}'] - globals()[f'x_{j}{k}'] + globals()[f'x_{i}{k}'] >= 0)
                    self.model.addConstr(-globals()[f'x_{i}{j}'] + globals()[f'x_{j}{k}'] + globals()[f'x_{i}{k}'] >= 0)
        end = datetime.now()
        print(f'function add_constraints ended and took {end-start} seconds')

# ilp_obj = ILP("C:/Users/97252/Documents/year_4/sadna/tests/network.dat")
ilp_obj= ILP("C://Users//97252//Documents//year_4//sadna//tests//edges_tuple.list")

for v in ilp_obj.model.getVars():
    print('%s %g ' % (v.VarName, v.X))
for c in ilp_obj.model.getConstrs():
    print(c.ConstrName, c.Slack)
print('Obj: %g ' % ilp_obj.model.ObjVal)


