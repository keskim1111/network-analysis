import logging
import networkx as nx
import struct
from utils.helpers import timeit, create_graph_from_edge_file
import os

def create_mapping(edge_file):
    d = dict()
    G = create_graph_from_edge_file(edge_file)
    i = 0
    nodes = sorted(G.nodes)
    for node in nodes:
        d[i] = node
        i += 1
    return d


@timeit
def read_binary_network_input(fileName, edgesFile=None):
    """
    :param: fileName of a binary file of the following format:
            The first value represents the number of nodes in the network, n = |V |.
            The second value represents the number of edges of the first node, i.e., k1. It is followed by
            the k1 indices of its neighbors, in increasing order.
            The next value is k2, followed by the k2 indices of the neighbors of the second node, then k3
            and its k3 neighbors, and so on until node n.
    :return: a networkX graph created based on the binary file
    """
    G = nx.Graph()
    f = open(fileName, "rb")
    try:
        if edgesFile is not None:
            mapping = create_mapping(edgesFile)
        num_of_nodes_byte = f.read(4)
        num_of_nodes = struct.unpack('i', num_of_nodes_byte)[0]
        for i in range(num_of_nodes):
            if edgesFile is not None:
                node = mapping[i]
            else:
                node = i
            num_of_neighbors_byte = f.read(4)
            num_of_neighbors = struct.unpack('i', num_of_neighbors_byte)[0]
            for j in range(num_of_neighbors):
                neighbor_byte = f.read(4)
                neighbor = struct.unpack('i', neighbor_byte)[0]
                G.add_edge(node, neighbor)
    finally:
        f.close()
    return G


@timeit
def read_binary_network_output(fileName):
    """
    :param: fileName of a binary file of the following format:
            The first value represents the number of groups in the division.
            The second value represents the number of nodes in the first group, followed by the indices
            of the nodes in the group, in increasing order.
            The next value is the number of nodes in the second group, followed by the indices of the
            nodes in group, then the number of nodes and indices of nodes in the third group, and so
            on until the last group

    :return: list of lists (comm)
    """
    f = open(fileName, "rb")
    res = []
    try:
        num_of_groups_byte = f.read(4)
        num_of_groups = struct.unpack('i', num_of_groups_byte)[0]
        for i in range(num_of_groups):
            group = []
            num_of_nodes_in_group_byte = f.read(4)
            num_of_nodes_in_group = struct.unpack('i', num_of_nodes_in_group_byte)[0]
            for j in range(num_of_nodes_in_group):
                group_member_byte = f.read(4)
                group_member = struct.unpack('i', group_member_byte)[0]
                group.append(group_member)
            res.append(group)
    finally:
        f.close()
    return res

@timeit
def create_binary_network_file(G, path, title="graph"):
    """
    :param: G - a networkX graph created based on the binary file
    :return: A path to a binary file created in the following format:
            The first value represents the number of nodes in the network, n = |V |.
            The second value represents the number of edges of the first node, i.e., k1. It is followed by
            the k1 indices of its neighbors, in increasing order.
            The next value is k2, followed by the k2 indices of the neighbors of the second node, then k3
            and its k3 neighbors, and so on until node n.
    """
    file_name = f'{title}.in'
    f = open(os.path.join(path, file_name), "wb")
    try:
        nodes_list = sorted(G.nodes())
        num_of_nodes = len(nodes_list)
        f.write(struct.pack('i', num_of_nodes))
        for node in nodes_list:
            neighbors = sorted(list(G.neighbors(node)))
            num_of_neighbors = len(neighbors)
            f.write(struct.pack('i', num_of_neighbors))
            for neighbor in neighbors:
                f.write(struct.pack('i', int(neighbor)))
    finally:
        f.close()
    return os.path.join(path, file_name)


@timeit
def create_binary_communities_file(communities, path, title="communities"):
    """
    :param: communities - list of lists - each list represents a community
            path - to save the created binary file
    :return: A path to a binary file created in the following format:
            The first value represents the number of groups in the division.
            The second value represents the number of nodes in the first group, followed by the indices
            of the nodes in the group, in increasing order.
            The next value is the number of nodes in the second group, followed by the indices of the
            nodes in group, then the number of nodes and indices of nodes in the third group, and so
            `on until the last group
    """
    file_name = f'{title}.in'
    f = open(os.path.join(path, file_name), "wb")
    num_of_groups = len(communities)
    try:
        f.write(struct.pack('i', num_of_groups))
        for i in range(num_of_groups):
            group = communities[i]
            num_of_nodes_in_group = len(group)
            f.write(struct.pack('i', num_of_nodes_in_group))
            for j in group:
                node = j
                f.write(struct.pack('i', node))
    finally:
        f.close()
    return os.path.join(path, file_name)


def create_for_esty_from_edges(edge_list):
    logging.debug(f"The path is {edge_list}")
    G = create_graph_from_edge_file(edge_list)
    return create_binary_network_file(G)



