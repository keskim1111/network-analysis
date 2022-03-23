from networkx.generators.community import LFR_benchmark_graph
import networkx as nx
from LFRBenchmark.LFRBenchmark import generate_lfr_benchmarks
from os.path import abspath
from consts import edges_files


def create_random_network(n, mu, tau1=2, tau2=1.1, average_degree=25, min_community=50):
    max_degree = int(n / 10)
    return LFR_benchmark_graph(
        n=n, tau1=tau1, tau2=tau2, mu=mu, average_degree=average_degree, max_degree=max_degree,
        min_community=min_community, max_community=int(n / 10)
    )


def create_lfr_benchmarks():
    generate_lfr_benchmarks()


def create_graph_from_edge_list(filename):
    '''
    :param filename:
    :return: a networkX graph from the file
    '''
    G = nx.Graph()
    with open(filename) as file:
        while line := file.readline():
            edge = tuple(line.rstrip().split())
            G.add_edge(*edge)
    return G

# TODO decide on a format
def read_clusters_file(filename):
    '''
    :param filename:
    :return:
    '''
    pass



