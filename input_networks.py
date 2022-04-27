from networkx.generators.community import LFR_benchmark_graph
import networkx as nx
from LFRBenchmark.LFRBenchmark import generate_lfr_benchmarks
from collections import defaultdict
import os, pickle
from binary_files import create_binary_network_file
from helpers import init_results_folder


def create_random_network(n=1000, mu=0.4, tau1=2, tau2=1.1, average_degree=15, min_community=20, max_degree=50,max_community =50):
    return LFR_benchmark_graph(
        n=n, tau1=tau1, tau2=tau2, mu=mu, average_degree=average_degree, max_degree=max_degree,
        min_community=min_community, max_community=max_community
    )


def read_communities_file(path):
    '''
        :param path:
        :return: a list of lists of communities
        '''
    community_dict = defaultdict(list)
    with open(path) as file:
        while line := file.readline():
            node, community = line.rstrip().split()
            community_dict[community].append(node)
    return list(community_dict.values())


def create_lfr_benchmarks():
    generate_lfr_benchmarks()


def create_graph_from_edge_file(filename):
    '''
    :param filename:
    :return: a networkX graph from the file
    '''
    G = nx.Graph()
    with open(filename) as file:
        while line := file.readline():
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

yeast_edges = "C:\\Users\\kimke\\OneDrive\\Documents\\4th year\\semeter B\\Biological networks sadna\\network-analysis\\Benchmarks\\Yeast\\edges.txt"


def create_graph_from_edge_strings_file(filename):
    '''
    :param filename:
    :return: a networkX graph from the file
    '''
    G = nx.Graph()
    dict_str_to_num = dict()
    i = 0
    with open(filename) as file:
        try:
            while line := file.readline():
                node1, node2 = line.rstrip().split()
                if node1 not in dict_str_to_num:
                    dict_str_to_num[node1] = i
                    i += 1
                if node2 not in dict_str_to_num:
                    dict_str_to_num[node2] = i
                    i += 1
                node1_num = dict_str_to_num[node1]
                node2_num = dict_str_to_num[node2]
                G.add_edge(node1_num, node2_num)
        except ValueError:
            print(line)
            raise ValueError
    return G


# Before running neumann C code - creating graph from LFR benchmark networkx
def create_networkx_graph_and_save_to_folder(params_dict, save_path=init_results_folder()):
    '''
    :param: param_dict - dictionary of parameters to create networkx graph, save_path - path to save results
    :example: param_dict={"n": 1000, "mu": 0.1, "tau1": 2, "tau2": 1.1, "average_degree": 25, "minimum_community": 50}
    :return: create pickle file objects in save_path - edges.list, real_communities.dict, params.dict
    '''
    n = params_dict["n"]
    max_degree = int(n / 10)
    max_community = int(n / 10)

    G = LFR_benchmark_graph(
        n=n, tau1=params_dict["tau1"], tau2=params_dict["tau2"], mu=params_dict["mu"], average_degree=params_dict["average_degree"],
        min_community=params_dict["minimum_community"], max_degree=max_degree, max_community=max_community
    )

    real_communities = {frozenset(G.nodes[v]["community"]) for v in G}
    real_modularity = nx.algorithms.community.modularity(G, real_communities)
    print(f'real_modularity: {real_modularity}')
    binary_network = create_binary_network_file(G, save_path, title=os.path.basename(save_path))

    # saving results for future use
    with open(os.path.join(save_path, "edges.list"), "wb") as f:
        pickle.dump(G.edges, f)
    with open(os.path.join(save_path, "real_communities.dict"), "wb") as f:
        pickle.dump(real_communities, f)
    with open(os.path.join(save_path, "params.dict"), "wb") as f:
        pickle.dump(params_dict, f)
    print(f'saved results in {save_path}')

    return real_communities

if __name__ == '__main__':
    create_graph_from_edge_strings_file(yeast_edges)
