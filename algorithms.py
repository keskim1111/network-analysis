import networkx as nx
from ilp import ILP
# TODO read more here
# https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html?highlight=louvain#networkx.algorithms.community.louvain.louvain_communities
from helpers import timeit, timeout


@timeit
def louvain(G):
    return nx.algorithms.community.louvain_communities(G)


# TODO read more here
# https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.centrality.girvan_newman.html?highlight=newman#networkx.algorithms.community.centrality.girvan_newman
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
