import time
from collections import defaultdict
from datetime import datetime
import networkx as nx
import pickle, os
import logging
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
        logging.debug('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsed_time * 1_000)))
        return result

    return new_func


def current_time():
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y--%H-%M-%S")
    return dt_string


def write_to_file(file, content, is_log=False):
    now = datetime.now()
    if is_log:
        current_time = now.strftime("%H:%M:%S")
        line = f"[{current_time}]: {content}\n"
        print(line)
    else:
        line = f"{content}"
    with open(file, "a") as f:
        f.write(line)
    return file


def create_sub_graphs_from_communities(G, communities):
    sub_graphs = []
    for community in communities:
        sub_graphs.append(G.subgraph(community))
    return sub_graphs


def init_results_folder(init_path, folder_name=""):
    if not os.path.isdir(init_path):
        os.mkdir(init_path)
    if len(folder_name) == 0:  # Create new folder according to current date
        curr_res_path = os.path.join(init_path, f"{current_time()}")
    else:  # Create new folder according to folder_name
        curr_res_path = os.path.join(init_path, folder_name)
    if not os.path.isdir(curr_res_path):
        os.mkdir(curr_res_path)
    return os.path.join(os.getcwd(), curr_res_path)


def read_graph_files(graph_path, run_obj, write_to_files=False):
    '''
    :param graph_path: path to graph built from nodes that are strings
    :return: a networkX graph created from the strings edges file, with
    nodes that are numbers.
    a list of communities with numbers created from the community strings file
    a dict that maps the strings of the nodes to numbers
    '''
    edges_file = os.path.join(graph_path, run_obj.network_file_name)
    clusters_file = os.path.join(graph_path, run_obj.community_file_name)

    G = nx.Graph()
    dict_str_to_num = dict()
    dict_num_to_str = dict()
    i = 0
    clusters = {}
    with open(clusters_file) as f:
        while line := f.readline():
                if len( line.rstrip().split("\t")) > 2:
                    logging("ERROR")
                node, community = line.rstrip().split("\t")
                if node not in dict_str_to_num:
                    dict_str_to_num[node] = i
                    dict_num_to_str[i]=node
                    G.add_node(i)
                    i += 1
                if community not in clusters:
                    clusters[community] = []
                clusters[community].append(dict_str_to_num[node])

    clusters_list = [nodes for nodes in clusters.values()]

    with open(edges_file) as file:
        while line := file.readline():
                str_node1, str_node2 = line.rstrip().split("\t")
                # map str node name to a number
                num_node1 = dict_str_to_num[str_node1]
                num_node2 = dict_str_to_num[str_node2]
                G.add_edge(num_node1, num_node2)


    if write_to_files:
        with open(os.path.join(graph_path, "clusters.list"), "wb") as f:
            pickle.dump(clusters_list, f)


        # save values
        with open(os.path.join(graph_path, "edges.list"), "wb") as f:
            pickle.dump(G.edges, f)

        with open(os.path.join(graph_path, "str_to_num.dict"), "wb") as f:
            pickle.dump(dict_str_to_num, f)

    return G, clusters_list, dict_num_to_str


def _pickle(fp, object="", is_load=False, is_dump=False):
    if is_dump:
        with open(fp, "wb") as f:
            pickle.dump(object, f)
    elif is_load:
        with open(fp, "rb") as f:
            return pickle.load(f)
    return None

def prompt_file(path):
    path = os.path.realpath(path)
    os.startfile(path)

def create_graph_from_edge_list(edges_list):
    '''
    :param python list of sets of edges:
    :return: a networkX graph from the file
    '''
    G = nx.Graph()
    for node1, node2 in edges_list:
        G.add_edge(int(node1), int(node2))
    return G

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

def create_random_network(n=1000, mu=0.4, tau1=2, tau2=1.1, average_degree=15, min_community=20, max_degree=50,max_community =50):
    return nx.LFR_benchmark_graph(
        n=n, tau1=tau1, tau2=tau2, mu=mu, average_degree=average_degree, max_degree=max_degree,
        min_community=min_community, max_community=max_community
    )


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