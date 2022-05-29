import logging
import random

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

from algorithms.modified_louvain import _gen_graph


def convert_mega_nodes_to_communities(G, mega_communities_partition: [list]):
    final_communities = []
    attribute_dict = nx.get_node_attributes(G, "nodes")
    # no partition occurred, every mega node is a community
    if len(mega_communities_partition) == 1:
        for mega_node in mega_communities_partition[0]:
            final_communities.append(attribute_dict.get(mega_node))
    # partition occurred, some mega nodes are together
    else:
        for mega_community in mega_communities_partition:
            regular_com = []
            for mega_node in mega_community:
                regular_com += attribute_dict.get(mega_node)
            final_communities.append(regular_com)
        # if len(final_com) == 1:
        #     return final_com[0]
    return final_communities


def split_mega_nodes(G, mega_graph, n: int, is_random=False, is_min_cut=False, is_modularity = False):
    num_original_mega_nodes = mega_graph.number_of_nodes()
    mega_nodes = mega_graph.nodes()
    attribute_dict = nx.get_node_attributes(mega_graph, "nodes")
    if num_original_mega_nodes >= n:
        logging.info("Didnt split mega_nodes")
        return mega_graph
    new_partition = []
    for i,mega_node in enumerate(mega_nodes):
        if len(new_partition) + (num_original_mega_nodes-i) < n:
            if is_random:
                communities = random_split_mega_node(mega_node, attribute_dict)
            elif is_min_cut:
                communities = min_cut_split_mega_node(G, mega_node, attribute_dict)
            elif is_modularity:
                communities = modularity_split_mega_node(G,mega_node,attribute_dict)
            new_partition += communities
        else:
            new_partition.append(list(attribute_dict.get(mega_node)))
        graph = G.__class__()
        graph.add_nodes_from(G)
        graph.add_weighted_edges_from(G.edges(data="weight", default=1))
    new_graph = _gen_graph(graph, new_partition)
    return new_graph

# --------------------------Random split----------------------------------

def random_split_mega_node(mega_node, attribute_dict):
    initial_nodes_partition = list(attribute_dict.get(mega_node))
    num_of_nodes = len(initial_nodes_partition)
    if num_of_nodes > 1:
        random.shuffle(initial_nodes_partition)
        nodes_two_partition = [initial_nodes_partition[:num_of_nodes // 2],
                               initial_nodes_partition[(num_of_nodes // 2):]]
        return nodes_two_partition
    return initial_nodes_partition

# --------------------------min-cut split----------------------------------
def min_cut_split_mega_node(G, mega_node, attribute_dict):
    community = list(attribute_dict.get(mega_node))
    sub_graph = G.subgraph(community)
    nx.set_edge_attributes(sub_graph, 1, "capacity")
    c, partition = nx.minimum_cut(sub_graph,community[0],community[1])
    return partition

# --------------------------modularity split----------------------------------
def modularity_split_mega_node(G, mega_node, attribute_dict):
    community = list(attribute_dict.get(mega_node))
    sub_graph = G.subgraph(community)
    communities = greedy_modularity_communities(sub_graph)
    return [list(x) for x in communities]

if __name__ == '__main__':
    pass
