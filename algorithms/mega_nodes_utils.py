import logging
import random, os

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

from algorithms.algorithms import louvain
from algorithms.split_community.our_version import Newman_ILP
from algorithms.split_community.roded_version import Newman_ILP_RODED
from algorithms.modified_louvain import _gen_graph
from helpers import timeit
from algorithms.neumann_utils import split_communities_with_newman, get_neumann_communities
from utils.binary_files import create_binary_communities_file, create_binary_network_file


def unite_mega_nodes_and_convert2communities(G, mega_communities_partition: [list]):
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
    logging.debug(f"***Number of original mega nodes before split is {num_original_mega_nodes}***")
    mega_nodes = mega_graph.nodes()
    attribute_dict = nx.get_node_attributes(mega_graph, "nodes")
    if num_original_mega_nodes >= n:
        logging.debug("Didnt split mega_nodes")
        return mega_graph
    new_partition = []
    logging.debug(f"split method used is {run_obj.split_method}!!")
    for i, mega_node in enumerate(mega_nodes):
        community = list(attribute_dict.get(mega_node))
        logging.debug(f"Trying splitting the {i}/{len(mega_nodes)} mega node!")
        logging.debug(f"{len(community)} nodes in current mega node")

        if len(new_partition) + (num_original_mega_nodes - i) < n:
            communities = run_obj.split_methods[run_obj.split_method](G, community, run_obj)
            if len(communities) > 1:
                logging.debug(f"splitted current node")
                for i in range(len(communities)):
                    logging.debug(f"{len(communities[i])} nodes in current {i}/{len(communities)}")
                new_partition += communities
            else:
                new_partition.append(community)
        else:
            new_partition.append(list(attribute_dict.get(mega_node)))
    graph = G.__class__()
    graph.add_nodes_from(G)
    graph.add_weighted_edges_from(G.edges(data="weight", default=1))
    logging.debug(f"***Number of communities after split is {len(new_partition)}***")
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
def ilp_split_mega_node(G, mega_community_nodes, run_obj):
    n = len(mega_community_nodes)
    if n > run_obj.max_mega_node_split_size:
        logging.debug(f"Skipped dividing mega nodes, too big: {n} nodes> {run_obj.max_mega_node_split_size} nodes!")
        return [mega_community_nodes]
    sub_graph = G.subgraph(mega_community_nodes)
    obj = Newman_ILP_RODED(sub_graph,TimeLimit=run_obj.TimeLimit)
    logging.debug(f"Split mega node!")
    return obj.communities

@timeit
def ilp_split_mega_node_whole_graph(G, mega_community_nodes, run_obj):
    n = len(mega_community_nodes)
    if n > run_obj.max_mega_node_split_size:
        logging.debug(f"Skipped dividing mega nodes, too big: {n} nodes> {run_obj.max_mega_node_split_size} nodes!")
        return [mega_community_nodes]
    obj = Newman_ILP_RODED(G, nodes_list=mega_community_nodes, TimeLimit=run_obj.TimeLimit)
    logging.debug(f"Split mega node!")
    return obj.communities


@timeit
def newman_split_mega_nodes_whole_graph(network_obj, mega_graph):
    communities = unite_mega_nodes_and_convert2communities(mega_graph, [mega_graph.nodes()])
    communities_list_sorted = []
    for com in communities:
        com_sorted = list(com)
        com_sorted.sort(reverse=True)
        communities_list_sorted.append(com_sorted)
    logging.debug(f"***Number of communities before split is {len(communities_list_sorted)}***")

    new_communities = split_communities_with_newman(network_obj.save_directory_path, network_obj.network_name, network_obj.graph_binary_input_fp, communities_list_sorted)
    G = network_obj.G
    graph = G.__class__()
    graph.add_nodes_from(G)
    graph.add_weighted_edges_from(G.edges(data="weight", default=1))
    logging.debug(f"***Number of communities after split is {len(new_communities)}***")
    new_graph = _gen_graph(graph, new_communities)
    return new_graph


def create_mapping_nodes(community):
    node_to_int_mapping = {}
    int_to_node_mapping = {}
    for i in range(len(community)):
        node = community[i]
        node_to_int_mapping[node] = i
        int_to_node_mapping[i] = node
    return node_to_int_mapping, int_to_node_mapping


def newman_split_mega_nodes_sub_graph(network_obj, mega_graph):
    G = network_obj.G
    communities = unite_mega_nodes_and_convert2communities(mega_graph, [mega_graph.nodes()])
    logging.info(f"***Number of communities before split is {len(communities)}***")
    communities_after_split = []
    for i in range(len(communities)):
        com = list(communities[i])
        # com.sort(reverse=True) # not sure it needs to be sorted ?
        node_to_int_mapping, int_to_node_mapping = create_mapping_nodes(com)
        sub_graph = G.subgraph(list(int_to_node_mapping.keys()))

        cur_binary_file_name = f'{network_obj.network_name}-{i}'
        create_binary_network_file(sub_graph, network_obj.save_directory_path, title=cur_binary_file_name)
        cur_binary_fp = os.path.join(network_obj.save_directory_path, cur_binary_file_name)

        # new_communities = get_neumann_communities(network_obj.save_directory_path, network_obj.network_name, binary_input_fp=f'{cur_binary_fp}.in', binary_output_fp=f'{cur_binary_fp}.out')
        new_communities = split_communities_with_newman(network_obj.save_directory_path, network_obj.network_name,
                                                        f'{cur_binary_fp}.in', [list(int_to_node_mapping.keys())])

        communities_after_split+=new_communities

    # new_communities = split_communities_with_newman(network_obj.save_directory_path, network_obj.network_name,
    #                                                 network_obj.graph_binary_input_fp, communities_list_sorted)
    logging.info(f"***Number of communities after split is {len(communities_after_split)}***")
    graph = G.__class__()
    graph.add_nodes_from(G)
    graph.add_weighted_edges_from(G.edges(data="weight", default=1))
    new_graph = _gen_graph(graph, communities_after_split)
    return new_graph

