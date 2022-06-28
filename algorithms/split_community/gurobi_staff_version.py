from collections import defaultdict
import gurobipy as gp
from gurobipy import GRB
from helpers import timeit
import networkx as nx

'''
Implementation according to 
https://support.gurobi.com/hc/en-us/community/posts/6863277481233-Newman-iteration-foamalation
'''
class Newman_ILP2:
    def __init__(self, G, weight=None, IntFeasTol=None, TimeLimit=None):
        """
        :param G: networkx graph
        :param nodes:
        """
        self.nodes_list = list(G.nodes)
        self.num_of_nodes = len(self.nodes_list)
        self.G = G
        self.weight = weight
        self.model = gp.Model("modularity")
        # params
        if IntFeasTol is not None:
            self.model.setParam("IntFeasTol", IntFeasTol)
        if TimeLimit is not None:
            self.model.setParam("TimeLimit", TimeLimit)
        self.set_ilp()  # setting objective function and constraints and optimizing
        self.communities = self.get_communities()

    @timeit
    def set_ilp(self):
        n = self.G.number_of_nodes()
        m = self.G.size(weight=self.weight)
        A = nx.adjacency_matrix(self.G).toarray()
        k = [self.G.degree(i) for i in range(n)]
        x = self.model.addVars(n, vtype=GRB.BINARY, name="x")
        s = self.model.addVars(n, lb=-1, ub=1, vtype=GRB.INTEGER, name="s")

        # Define s_i=2x_i -1 such that if x_i=1, then s_i=1 and
        # if x_i=0, then s_i=-1
        self.model.addConstrs(
            (s[i] == 2 * x[i] - 1 for i in range(n)), name="connect_x_s_constr"
        )
        # Define the objective function
        Q = gp.QuadExpr()
        for i in range(n):
            for j in range(n):
                Q += (A[i, j] - k[i] * k[j] / m) * (s[i] * s[j] + 1)
        Q *= 0.5
        self.model.setObjective(Q, sense=GRB.MAXIMIZE)

        self.model.optimize()



    def get_communities(self):
        communities = defaultdict(set)
        for v in self.model.getVars():
            print(v)
            st = v.VarName
            if st.startswith("s"):
                node = st[st.find("[") + 1:st.find("]")]
                communities[str(v.X)].add(int(node))
        # pprint(communities)
        com_sets = communities.values()
        if len(com_sets) > 1:
            return list([list(v) for v in communities.values()])
        return list(com_sets)
