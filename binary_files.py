import networkx as nx
import struct

from helpers import timeit, current_time

@timeit
def read_binary_network(fileName):
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
        num_of_nodes_byte = f.read(4)
        num_of_nodes = struct.unpack('i', num_of_nodes_byte)[0]
        # print(f"num_of_nodes {num_of_nodes}")
        for i in range(num_of_nodes):
            num_of_neighbors_byte = f.read(4)
            num_of_neighbors = struct.unpack('i', num_of_neighbors_byte)[0]
            # print(f"*num_of_neighbors of {i} is {num_of_neighbors}")
            for j in range(num_of_neighbors):
                neighbor_byte = f.read(4)
                neighbor = struct.unpack('i', neighbor_byte)[0]
                G.add_edge(i, neighbor)
            # print(f"num_of_neighbors of {i} is {len([n for n in G.neighbors(i)])}")
    finally:
        f.close()
    return G


def create_binary_network_file(G):
    """
    :param: G - a networkX graph created based on the binary file
    :return: A path to a binary file created in the following format:
            The first value represents the number of nodes in the network, n = |V |.
            The second value represents the number of edges of the first node, i.e., k1. It is followed by
            the k1 indices of its neighbors, in increasing order.
            The next value is k2, followed by the k2 indices of the neighbors of the second node, then k3
            and its k3 neighbors, and so on until node n.
    """
    file_name = f'{current_time()}-graph.in'
    f = open(file_name, "wb")
    try:
        nodes_list = sorted(G.nodes())
        num_of_nodes = len(nodes_list)
        f.write(struct.pack('i', num_of_nodes))
        for node in nodes_list:
            neighbors = sorted(list(G.neighbors(node)))
            num_of_neighbors = len(neighbors)
            f.write(struct.pack('i', num_of_neighbors))
            for neighbor in neighbors:
                f.write(struct.pack('i', neighbor))
    finally:
        f.close()
    return file_name

if __name__ == '__main__':
    path = 'graph.in'
    G = read_binary_network(path)
    print(f"##### G ##### {G}")
    g_nodes = G.nodes
    g_edges = G.edges

    path2 = create_binary_network_file(G)
    G2 = read_binary_network(path2)
    print(f"##### G2 ##### {G2}")
    g2_nodes = G2.nodes
    g2_edges = G2.edges

    assert g_nodes == g2_nodes
    assert g_edges == g2_edges
    diff = nx.difference(G,G2)
    assert len(diff.edges) == 0
