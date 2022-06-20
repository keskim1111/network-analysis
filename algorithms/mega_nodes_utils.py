import logging
import random

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

from algorithms.algorithms import louvain
from algorithms.ilp_split_community.our_version import Newman_ILP
from algorithms.ilp_split_community.roded_version import Newman_ILP_RODED
from algorithms.modified_louvain import _gen_graph
from helpers import timeit


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


def split_mega_nodes(G, mega_graph, n: int, run_obj):
    num_original_mega_nodes = mega_graph.number_of_nodes()
    mega_nodes = mega_graph.nodes()
    attribute_dict = nx.get_node_attributes(mega_graph, "nodes")
    if num_original_mega_nodes >= n:
        logging.info("Didnt split mega_nodes")
        return mega_graph
    new_partition = []
    logging.info(f"split method used is {run_obj.split_method}!!")
    for i, mega_node in enumerate(mega_nodes):
        community = list(attribute_dict.get(mega_node))
        logging.info(f"Trying splitting the {i}/{len(mega_nodes)} mega node!")
        logging.info(f"{len(community)} nodes in current mega node")

        if len(new_partition) + (num_original_mega_nodes - i) < n:
            communities = run_obj.split_methods[run_obj.split_method](G, community, run_obj)
            if len(communities) > 1:
                new_partition += communities
            else:
                new_partition.append(community)
        else:
            new_partition.append(list(attribute_dict.get(mega_node)))
        graph = G.__class__()
        graph.add_nodes_from(G)
        graph.add_weighted_edges_from(G.edges(data="weight", default=1))
    logging.info(f"Number of communities after split is {len(new_partition)}")
    new_graph = _gen_graph(graph, new_partition)
    return new_graph


# --------------------------Random split----------------------------------
@timeit
def random_split_mega_node(G, mega_community_nodes,run_obj):
    num_of_nodes = len(mega_community_nodes)
    if num_of_nodes > 1:
        random.shuffle(mega_community_nodes)
        nodes_two_partition = [mega_community_nodes[:num_of_nodes // 2],
                               mega_community_nodes[(num_of_nodes // 2):]]
        return nodes_two_partition
    return mega_community_nodes


# --------------------------min-cut split----------------------------------
@timeit
def min_cut_split_mega_node(G, mega_community_nodes,run_obj):
    sub_graph = G.subgraph(mega_community_nodes)
    nx.set_edge_attributes(sub_graph, 1, "capacity")
    c, partition = nx.minimum_cut(sub_graph, mega_community_nodes[0], mega_community_nodes[1])
    return partition


# --------------------------modularity split----------------------------------
@timeit
def modularity_split_mega_node(G, mega_community_nodes,run_obj):
    sub_graph = G.subgraph(mega_community_nodes)
    communities = greedy_modularity_communities(sub_graph)
    return [list(x) for x in communities]


# --------------------------louvain split----------------------------------
@timeit
def louvain_split_mega_node(G, mega_community_nodes,run_obj):
    sub_graph = G.subgraph(mega_community_nodes)
    communities = louvain(sub_graph)
    return communities


# --------------------------Newman split----------------------------------
@timeit
def newman_split_mega_node(G, mega_community_nodes, run_obj):
    n = len(mega_community_nodes)
    if n > run_obj.max_mega_node_split_size:
        logging.info(f"Skipped dividing mega nodes, too big: {n} nodes> {run_obj.max_mega_node_split_size} nodes!")
        return [mega_community_nodes]
    sub_graph = G.subgraph(mega_community_nodes)
    obj = Newman_ILP_RODED(sub_graph,TimeLimit=run_obj.TimeLimit)
    logging.info(f"Split mega node!")
    return obj.communities


if __name__ == '__main__':
    pass
