from networkx.generators.community import LFR_benchmark_graph
import networkx as nx
from collections import defaultdict
import os, pickle
from helpers import init_results_folder
from consts import RESULTS_FOLDER, yeast_path, arabidopsis_path


from helpers import timeit


def create_random_network(n=1000, mu=0.4, tau1=2, tau2=1.1, average_degree=15, min_community=20, max_degree=50,max_community =50):
    return LFR_benchmark_graph(
        n=n, tau1=tau1, tau2=tau2, mu=mu, average_degree=average_degree, max_degree=max_degree,
        min_community=min_community, max_community=max_community
    )


@timeit
def read_communities_file(path):
    '''
        :param path:
        :return: a list of lists of communities
        '''
    community_dict = defaultdict(list)
    with open(path) as file:
        lines = file.readlines()
        for line in lines:
            node, community = line.rstrip().split()
            community_dict[community].append(int(node))
    return list(community_dict.values())


@timeit
def create_graph_from_edge_file(filename):
    '''
    :param filename:
    :return: a networkX graph from the file
    '''
    G = nx.Graph()
    with open(filename) as file:
        lines = file.readlines()
        for line in lines:
            node1, node2 = line.rstrip().split()
            G.add_edge(int(node1),int(node2))
    return G

def create_graph_from_edge_list(edges_list):
    '''
    :param python list of sets of edges:
    :return: a networkX graph from the file
    '''
    G = nx.Graph()
    for node1, node2 in edges_list:
        G.add_edge(int(node1), int(node2))
    return G




if __name__ == '__main__':
    pass