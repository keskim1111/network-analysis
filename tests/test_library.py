from pprint import pprint

import networkx as nx

from algorithms.algorithms import louvain
from algorithms.ilp_split_community import Newman_ILP
from helpers import timeit
from input_networks import create_random_network

from algorithms.FF.community_newman import partition

@timeit
def trial():
    G = create_random_network(n=40, min_community=2, max_degree=2, max_community=2, average_degree=2)
    n = len(list(G.nodes))
    communities = louvain(G)
    print(f"com louvain: {len(communities)}")
    community_dict = dict()
    counter = 0
    for community in communities:
        for node in community:
            community_dict[node] = counter
        counter += 1
    new_communities = partition(G, one_iteration=True, community_dict=community_dict)
    print(f"com partition: {len(set(new_communities.values()))}")

    # pprint(new_communities)

def trial2():
    G = create_random_network(n=40, min_community=2, max_degree=2, max_community=2, average_degree=2)
    print(G)
    c = Newman_ILP(G)
    print(c.communities[0])
    print(len(c.communities[0]))
    print(c.communities[1])
    print(len(c.communities[1]))

if __name__ == '__main__':
    trial2()