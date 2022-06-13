from pprint import pprint

import networkx as nx

from input_networks import create_random_network

from algorithms.FF.community_newman import partition
def trial():
    G = create_random_network(n=40, min_community=2, max_degree=2, max_community=2, average_degree=2)
    comm_dict = partition(G,one_iteration=True)
    pprint(comm_dict)
    for comm in set(comm_dict.values()):
        print("Community %d"%comm)
        print(([node for node in comm_dict if comm_dict[node] == comm]))

if __name__ == '__main__':
    trial()