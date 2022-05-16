"""
I am using the following article - Discovering Communities in Networks: A Linear
Programming Approach Using Max-Min Modularity.
There is a similar article with more citings - Modularity-maximizing graph communities
via mathematical programming.
- the difference between the articles:
    the objective function in the second divides by 2. (1/2m)
"""
# TODO: make sure I can deal with inner edges
from evaluation import calc_modularity_manual

"""
# NEW: i changed the code - in a way that the nodes do NOT have to be continuous.
"""

import gurobipy as gp
from gurobipy import GRB
from helpers import timeit, timeout
import logging


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
        # params
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
        communities_per_node = {i: [i] for i in
                                self.nodes_list}  # i:com - com is the full community that node i is part of
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


def run_ilp_on_neumann(G, neumann_communities: [list], lp_critical: int, IntFeasTol=float(1e-5), withTimeLimit=False,
                       TimeLimit=0):
    final_communities = []
    num_communities_divided_by_ilp = 0
    num_communities_skipped_by_ilp = 0
    num_to_divide = len([len(x) <= lp_critical for x in neumann_communities])
    logging.info(f'num_to_divide: {num_to_divide}')
    for i in range(len(neumann_communities)):
        nodes_list = neumann_communities[i]
        num_nodes = len(nodes_list)
        logging.info(
            f'============== Iteration {i + 1}/{len(neumann_communities)}, subgraph size = {num_nodes} ================')
        if num_nodes > lp_critical:  # This community already reached maximal modularity - no need to divide more
            logging.info(f'num nodes {num_nodes} > lp_critical {lp_critical}, skipping.')
            num_communities_skipped_by_ilp += 1
            curr_communities = [nodes_list]
            final_communities += curr_communities
            continue

        curr_modularity = calc_modularity_manual(G, [nodes_list])  # Modularity before dividing more with ILP
        logging.info(f'Modularity of graph before {i + 1}th ILP iteration: {curr_modularity}')
        logging.info(f'============Trying to run ILP')
        if withTimeLimit:
            ilp_obj = ILP(G, nodes_list, IntFeasTol, TimeLimit=TimeLimit / num_to_divide)
        else:
            ilp_obj = ILP(G, nodes_list, IntFeasTol)
        new_modularity = calc_modularity_manual(G,
                                                ilp_obj.communities)  # TODO: make sure this is equal to ilp_obj.model.ObjVal
        logging.debug("ILP results===================================")
        logging.info(f'New modularity of graph after {i + 1}th ILP iteration: {new_modularity}')
        delta_Q = new_modularity - curr_modularity
        logging.info(f'Delta Q modularity is: {delta_Q}')
        if delta_Q > 0 and len(ilp_obj.communities) > 1:
            num_communities_divided_by_ilp += 1
            logging.info(
                f'Delta Q modularity is ++positive++: {delta_Q}. Adding ILP division to {len(ilp_obj.communities)} communities.')
            curr_communities = ilp_obj.communities  # New division
        else:
            logging.info(f'Delta Q modularity is --Negative-- or Zero: {delta_Q}.Not adding ILP division.')
            curr_communities = [nodes_list]  # Initial division

        logging.info(f'Num of curr_communities: {len(curr_communities)}')
        final_communities += curr_communities
    logging.info(
        f"Num of communities skipped by ILP (len(comm))> lp_critical) algo is {num_communities_skipped_by_ilp}/{len(neumann_communities)}")
    logging.info(
        f"Num of communities changed by ILP algo is {num_communities_divided_by_ilp}/{len(neumann_communities)}")
    return final_communities


def run_ilp_on_louvain(G, IntFeasTol=float(1e-5), withTimeLimit=False, TimeLimit=0):
    '''
    :param G: graph with MEGA nodes
    :return: communites
    '''
    nodes_list = G.nodes
    curr_modularity = calc_modularity_manual(G, [nodes_list])  # Modularity before dividing more with ILP
    logging.info(f'Modularity of graph before ILP iteration: {curr_modularity}')
    logging.info(f'============Trying to run ILP')
    if withTimeLimit:
        ilp_obj = ILP(G, nodes_list, IntFeasTol, TimeLimit=TimeLimit)
    else:
        ilp_obj = ILP(G, nodes_list, IntFeasTol)
    new_modularity = calc_modularity_manual(G,
                                            ilp_obj.communities)  # TODO: make sure this is equal to ilp_obj.model.ObjVal
    logging.debug("ILP results===================================")
    logging.info(f'New modularity of graph after ILP iteration: {new_modularity}')
    delta_Q = new_modularity - curr_modularity
    logging.info(f'Delta Q modularity is: {delta_Q}')
    if delta_Q > 0 and len(ilp_obj.communities) > 1:
        logging.info(
            f'Delta Q modularity is ++positive++: {delta_Q}. Adding ILP division to {len(ilp_obj.communities)} communities.')
        curr_communities = ilp_obj.communities  # New division
    else:
        logging.info(f'Delta Q modularity is --Negative-- or Zero: {delta_Q}.Not adding ILP division.')
        curr_communities = [nodes_list]  # Initial division

    logging.info(f'Num of curr_communities: {len(curr_communities)}')
    print(curr_communities)
    return curr_communities
