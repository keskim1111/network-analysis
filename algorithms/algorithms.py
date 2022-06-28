import networkx as nx
from algorithms.ilp.ilp_max_mod_union import ILP
from utils.helpers import timeit


@timeit
def louvain(G):
    return nx.algorithms.community.louvain_communities(G)

@timeit
def newman(G):
    comp = nx.algorithms.community.centrality.girvan_newman(G)
    return list(sorted(c) for c in next(comp))


def run_ilp(G):
    ilp_obj = ILP(G, is_networx_graph=True)
    return ilp_obj.communities


def algorithms_partition_for_colors(partition):
    color = 0
    color_partition = dict()
    for community in partition:
        for node in community:
            color_partition[node] = color
        color += 1
    return color_partition