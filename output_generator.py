import logging
import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from algorithms.algorithms import algorithms_partition_for_colors
from consts import RESULTS_FOLDER
from utils.evaluation import graph_conductance, jaccard, graph_sensitivity, graph_accuracy, calc_modularity_nx
from helpers import _pickle
from input_networks import read_communities_file

def create_visual_graph(G, partition, output, pos):
    pos = nx.spring_layout(G)
    cmap = cm.get_cmap('viridis', max(partition.values()) + 1)
    nx.draw_networkx_nodes(G, pos, partition.keys(), node_size=10, cmap=cmap,
                           node_color=list(partition.values()))
    # edges = nx.draw_networkx_edges(G, pos)
    plt.savefig(f"{output}.png", dpi=120)


def create_visual_graphs(G, algo_dict_partition, path):
    pos = nx.spring_layout(G)
    for algo in algo_dict_partition.keys():
        color_dict = algorithms_partition_for_colors(algo_dict_partition[algo]["partition"])
        cmap = cm.get_cmap('viridis', max(color_dict.values()) + 1)
        nx.draw_networkx_nodes(G, pos, color_dict.keys(), node_size=10, cmap=cmap,
                               node_color=list(color_dict.values()))
        nx.draw_networkx_edges(G, pos)
        plt.savefig(f"{path}\\{algo}.png", dpi=120)


def write_to_file(file, content):
    with open(file, "w") as f:
        f.write(content)
    return file


def create_output_folder(folder_name, G, edges_name="graph_edges"):
    path = f"{RESULTS_FOLDER}/{folder_name}"
    if not os.path.exists(f"{RESULTS_FOLDER}"):
        os.mkdir(f"{RESULTS_FOLDER}")
    os.mkdir(path)
    with open(f"{RESULTS_FOLDER}/{folder_name}/{edges_name}.txt", "w") as f:
        f.write(str(G.edges))
    return path

def create_df(data, columns, index):
    dfObj = pd.DataFrame(data, columns=columns, index=index)
    return dfObj


def generate_outputs(G, algo_dict, is_networkx=False, real_communities_path=None):
    data = []
    index = []
    if is_networkx:
        real_partition = {frozenset(G.nodes[v]["community"]) for v in G}
    else:
        real_partition = read_communities_file(real_communities_path)
    logging.debug(f"real partition: {real_partition}")
    for algo in algo_dict.keys():
        logging.debug(f'starting generating output for {algo}')
        partition = algo_dict[algo]["partition"]
        res = []
        index.append(algo)
        res.append(calc_modularity_nx(G, partition))
        res.append(graph_conductance(G, partition))
        res.append(jaccard(partition, real_partition))
        res.append(graph_sensitivity(real_partition, partition))
        res.append(graph_accuracy(real_partition, partition))
        data.append(res)
        logging.debug(f'finished generating output for {algo}')
    return data, index


def generate_outputs_for_community_list(G, real_communities_list, new_communities_list, algo=""):
    # TODO: dont the evaluation functions need to be inputed the real vs new in certain order? if yes it should be explained what the order should be in the function
    # TODO: maybe change calc_modularity_nx to calc_modularity_manual (bc not identical)
    evals = {}
    evals["algo"] = algo
    evals["modularity - real"] = calc_modularity_nx(G, real_communities_list)
    evals["modularity - algo"] = calc_modularity_nx(G, new_communities_list)
    logging.debug(f'modularity of algorithm = {evals["modularity - algo"]}')
    evals["jaccard"] = jaccard(new_communities_list, real_communities_list)
    try:
        evals["graph_conductance"] = graph_conductance(G, new_communities_list)
    except Exception as e:
        logging.error(f"couldnt calc graph_conductance with err: \n {e}")
        evals["graph_conductance"] = None
    evals["graph_sensitivity"] = graph_sensitivity(real_communities_list, new_communities_list)
    evals["graph_accuracy"] = graph_accuracy(real_communities_list, new_communities_list)
    evals["num communities - real"] = len(real_communities_list)
    evals["num communities - algo"] = len(new_communities_list)
    return evals


# TODO: add run time
def save_and_eval(save_dp,
                  evals_list,
                  algo,
                  network_obj,
                  run_obj,
                  communities,
                  time=None,
                  ):
    logging.debug("Saving communities object to folder")
    # Saving communities object to folder
    # _pickle(os.path.join(save_dp, f'{algo}.communities'), object=communities, is_dump=True)
    # Evaluate results and save to eval_dict
    eval_dict = generate_outputs_for_community_list(network_obj.G, network_obj.real_communities, communities, algo=algo)
    eval_dict["num_coms_divided"] = network_obj.num_coms_divided
    eval_dict["num_coms_skipped"] = network_obj.num_coms_skipped
    eval_dict["number_of_mega_nodes_before_split"] = network_obj.number_of_mega_nodes_before_split
    eval_dict["number_of_mega_nodes"] = network_obj.number_of_mega_nodes
    eval_dict["iterations"] = network_obj.iterations_number
    eval_dict["split_method"] = run_obj.split_method
    eval_dict["lp"] = run_obj.critical
    eval_dict["TimeLimit"] = run_obj.TimeLimit

    eval_dict["time-sec"] = time

    evals_list.append(eval_dict)


def create_data_dict(evals_list):
    """
    :param evals_list: list of eval dictionaries
    :return: data dict for df input
    """
    data_dict = {}
    for eval_dict in evals_list:
        for k, v in eval_dict.items():
            if not data_dict.get(k):
                data_dict[k] = []
            data_dict[k].append(v)
    return data_dict
