import functools
import time
from datetime import datetime
from consts import RESULTS_FOLDER, yeast_path
import os
import networkx as nx
import pickle, os

from threading import Thread
import functools


def timeout(timeout):
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, timeout))]

            def newFunc():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e

            t = Thread(target=newFunc)
            t.daemon = True
            try:
                t.start()
                t.join(timeout)
            except Exception as je:
                print('error starting thread')
                raise je
            ret = res[0]
            if isinstance(ret, BaseException):
                raise ret
            return ret

        return wrapper

    return deco


def timeit(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        print('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsed_time * 1_000)))
        return result

    return new_func


def current_time():
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y--%H-%M-%S")
    return dt_string

#
# def adjacency_matrix(G):
#     num_of_nodes = G.number_of_nodes()
#     adj_mat = [[0] * num_of_nodes for _ in range(num_of_nodes)]  # Initialize adjacency matrix
#     for i in range(num_of_nodes):
#         for j in range(num_of_nodes):
#
#     for i, j in G.edges:
#         adj_mat[i][j] = 1
#         adj_mat[j][i] = 1  # make sure it is undirected graph
#     return adj_mat


def create_sub_graphs_from_communities(G, communities):
    sub_graphs = []
    for community in communities:
        sub_graphs.append(G.subgraph(community))
    return sub_graphs

@timeit
def init_results_folder(init_path):
    if not os.path.isdir(init_path):
        os.mkdir(init_path)
    curr_res_path = os.path.join(init_path, f"{current_time()}")
    os.mkdir(curr_res_path)
    return os.path.join(os.getcwd(), curr_res_path)

def save_str_graph_in_good_format(graph_path):
    edges_file = os.path.join(graph_path, "edges.txt")
    clusters_file = os.path.join(graph_path, "clusters.txt")

    G = nx.Graph()
    dict_str_to_num = dict()
    i = 0
    with open(edges_file) as file:
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

    with open(os.path.join(graph_path, "edges.list"), "wb") as f:
        pickle.dump(G.edges, f)

    with open(os.path.join(graph_path, "str_to_num.dict"), "wb") as f:
        pickle.dump(dict_str_to_num, f)

    clusters = {}
    with open(clusters_file) as f:
        while line := f.readline():
            n, c = line.rstrip().split()
            if c not in clusters:
                clusters[c] = []
            clusters[c].append(dict_str_to_num[n])
    clusters_list = [nodes for nodes in clusters.values()]

    with open(os.path.join(graph_path, "clusters.list"), "wb") as f:
        pickle.dump(clusters_list, f)

# save_str_graph_in_good_format(yeast_path)
