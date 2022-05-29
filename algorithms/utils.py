import logging
import random

import networkx as nx

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


def random_split_mega_nodes(G, mega_graph, n: int):
    num_original_mega_nodes = mega_graph.number_of_nodes()
    attribute_dict = nx.get_node_attributes(mega_graph, "nodes")
    if num_original_mega_nodes >= n:
        logging.info("Didnt split mega_nodes")
        return mega_graph
    new_partition = []
    for mega_node in mega_graph.nodes:
        if len(new_partition) < n:
            two_communities = random_split_mega_node(mega_node, attribute_dict)
            new_partition += two_communities
        else:
            new_partition += list(attribute_dict.get(mega_node))
        graph = G.__class__()
        graph.add_nodes_from(G)
        graph.add_weighted_edges_from(G.edges(data="weight", default=1))
    new_graph = _gen_graph(graph, new_partition)
    return new_graph



def random_split_mega_node(mega_node, attribute_dict):
    initial_nodes_partition = list(attribute_dict.get(mega_node))
    num_of_nodes = len(initial_nodes_partition)
    if num_of_nodes > 1:
        random.shuffle(initial_nodes_partition)
        nodes_two_partition = [initial_nodes_partition[:num_of_nodes // 2],
                               initial_nodes_partition[(num_of_nodes // 2):]]
        return nodes_two_partition
    return initial_nodes_partition


if __name__ == '__main__':
    pass
