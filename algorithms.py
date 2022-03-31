import networkx as nx

# TODO read more here
# https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html?highlight=louvain#networkx.algorithms.community.louvain.louvain_communities
from helpers import timeit


@timeit
def louvain(G):
    return nx.algorithms.community.louvain_communities(G)


# TODO read more here
# https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.centrality.girvan_newman.html?highlight=newman#networkx.algorithms.community.centrality.girvan_newman
@timeit
def newman(G):
    comp = nx.algorithms.community.centrality.girvan_newman(G)
    return list(sorted(c) for c in next(comp))


def algorithms_partition_for_colors(partition):
    color = 0
    color_partition = dict()
    for community in partition:
        for node in community:
            color_partition[node] = color
        color += 1
    return color_partition
