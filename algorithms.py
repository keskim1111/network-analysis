import community as community_louvain


def louvain(G):
    return community_louvain.best_partition(G)


def create_partition(G):
    communities = {frozenset(G.nodes[v]["community"]) for v in G}
    partition = dict()
    col = 0
    for com in communities:
        for node in com:
            partition[node] = col
        col += 1
    return partition
