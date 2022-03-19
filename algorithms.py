import networkx as nx


# TODO read more here
# https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html?highlight=louvain#networkx.algorithms.community.louvain.louvain_communities
def louvain(G):
    return nx.algorithms.community.louvain_communities(G)


# TODO read more here
# https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.centrality.girvan_newman.html?highlight=newman#networkx.algorithms.community.centrality.girvan_newman
def newman(G):
    comp = nx.algorithms.community.centrality.girvan_newman(G)
    return tuple(sorted(c) for c in next(comp))


def create_partition(G):
    communities = {frozenset(G.nodes[v]["community"]) for v in G}
    partition = dict()
    col = 0
    for com in communities:
        for node in com:
            partition[node] = col
        col += 1
    return partition

