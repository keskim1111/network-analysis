import networkx as nx
import struct

from consts import edge_file
from evaluation import jaccard, graph_accuracy, graph_sensitivity, modularity
from input_networks import create_graph_from_edge_file, create_graph_from_edge_strings_file, \
    create_random_network
from helpers import timeit, current_time
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
            The first value represents the number of nodes in the network, n = |V |.
            The second value represents the number of edges of the first node, i.e., k1. It is followed by
            the k1 indices of its neighbors, in increasing order.
            The next value is k2, followed by the k2 indices of the neighbors of the second node, then k3
            and its k3 neighbors, and so on until node n.
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
def create_binary_network_file(G, path, title="bin", is_shanis_file=False):
    """
    :param: G - a networkX graph created based on the binary file
    :return: A path to a binary file created in the following format:
            The first value represents the number of nodes in the network, n = |V |.
            The second value represents the number of edges of the first node, i.e., k1. It is followed by
            the k1 indices of its neighbors, in increasing order.
            The next value is k2, followed by the k2 indices of the neighbors of the second node, then k3
            and its k3 neighbors, and so on until node n.
    """
    file_name = f'{title}-graph.in'
    f = open(os.path.join(path, file_name), "wb")
    try:
        nodes_list = sorted(G.nodes())
        num_of_nodes = len(nodes_list)
        f.write(struct.pack('i', num_of_nodes))
        for node in nodes_list:
            neighbors = sorted(list(G.neighbors(node)))
            if is_shanis_file:
                node -= 1
            num_of_neighbors = len(neighbors)
            f.write(struct.pack('i', num_of_neighbors))
            for neighbor in neighbors:
                if is_shanis_file:
                    neighbor -= 1
                f.write(struct.pack('i', int(neighbor)))
    finally:
        f.close()
    return os.path.join(path, file_name)


# TODO remove after
def create_for_esty_from_edges_strings(edge_list):
    print(f"The path is {edge_list}")
    G = create_graph_from_edge_strings_file(edge_list)
    print(G)
    return create_binary_network_file(G)


def create_for_esty_from_edges(edge_list):
    print(f"The path is {edge_list}")
    G = create_graph_from_edge_file(edge_list)
    return create_binary_network_file(G)


def compare_c_output_to_real(output_path, real_communities_path, real_edges_path):
    our_communities = read_binary_network_output(output_path)
    G = read_binary_network_input(real_edges_path)
    # real_communities = read_communities_file(real_communities_path)
    real_communities = real_communities_path
    # G = create_graph_from_edge_list(real_edges_path)
    print("###### Results ##########")
    print(f"num of our communities is: {len(our_communities)}")
    print(f"min size of a community (from ours): {min([len(group) for group in our_communities])}")
    print(f"max size of a community (from ours): {max([len(group) for group in our_communities])}")
    print(our_communities)
    print(f"num of  real communities is: {len(real_communities)}")
    print(real_communities)
    print("modularity is")
    print(modularity(G, our_communities))
    print("jaccard is")
    print(jaccard(our_communities, real_communities))
    print("graph_sensitivity is")
    print(graph_sensitivity(real_communities, our_communities))
    print("graph_accuracy is")
    print(graph_accuracy(real_communities, our_communities))
    Differences = [list(j) for j in {tuple(i) for i in real_communities} ^ {tuple(i) for i in our_communities}]
    print(f"diff is {Differences}")


def check_binary_from_edges_file():
    G = create_graph_from_edge_file(edge_file)
    path = create_binary_network_file(G, "1000_0.4_8_new")
    G2 = read_binary_network_input(path, edge_file)
    assert are_graphs_the_same(G, G2)


def check_lfr():
    n = 250
    mu = 0.1
    tau1 = 3
    tau2 = 1.5
    average_degree = 5
    min_com = 20
    G = create_random_network(n, mu, tau1, tau2, average_degree, min_com)
    path = create_binary_network_file(G)
    G2 = read_binary_network_input(path)
    assert are_graphs_the_same(G, G2)


def are_graphs_the_same(G, H):
    R = nx.difference(G, H)
    return len(R.edges) == 0



if __name__ == '__main__':
    pass
