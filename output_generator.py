import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from algorithms import newman, louvain, algorithms_partition_for_colors, run_ilp
from consts import RESULTS_FOLDER
from evaluation import graph_conductance, jaccard, graph_sensitivity, graph_accuracy, modularity
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


def create_pdf(df, path, params):
    fig, ax = plt.subplots()
    # hide axes
    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')
    ax.table(cellText=df.values, colLabels=df.columns, rowLabels=df.index, loc='center')
    fig.tight_layout()
    txt = ''.join([f"{val} param was {param}\n" for val, param in params.items()])
    plt.figtext(0.5, 0.1, txt, wrap=True, horizontalalignment='center', fontsize=9)
    plt.savefig(path)
    plt.close(fig)


def run_algos(G, with_ilp=False):
    if with_ilp:
        algo_dict = {"newman": {"func": newman}, "louvain": {"func": louvain}, "ilp": {"func": run_ilp}}
    else:
        algo_dict = {"newman": {"func": newman}, "louvain": {"func": louvain}}
    for algo in algo_dict.keys():
        print(f'running {algo}')
        partition = algo_dict[algo]["func"](G)
        algo_dict[algo]["partition"] = partition
        print(f'finished running {algo}')
    return algo_dict


def generate_outputs(G, algo_dict, is_networkx=False, real_communities_path=None):
    data = []
    index = []
    if is_networkx:
        real_partition = {frozenset(G.nodes[v]["community"]) for v in G}
    else:
        real_partition = read_communities_file(real_communities_path)
    print(f"real partition: {real_partition}")
    for algo in algo_dict.keys():
        print(f'starting generating output for {algo}')
        partition = algo_dict[algo]["partition"]
        res = []
        index.append(algo)
        res.append(modularity(G, partition))
        res.append(graph_conductance(G, partition))
        res.append(jaccard(partition, real_partition))
        res.append(graph_sensitivity(real_partition, partition))
        res.append(graph_accuracy(real_partition, partition))
        data.append(res)
        print(f'finished generating output for {algo}')
    return data, index


def generate_outputs_for_community_list(G, real_communities_list, new_communities_list):
    # TODO: dont the evaluation functions need to be inputed the real vs new in certain order? if yes it should be explained what the order should be in the function
    evals = {}
    evals["num communities - real"] = len(real_communities_list)
    evals["num communities - algo"] = len(new_communities_list)
    evals["modularity - real"] = modularity(G, real_communities_list)
    evals["modularity - algo"] = modularity(G, new_communities_list)
    evals["graph_conductance"] = graph_conductance(G, new_communities_list)
    evals["jaccard"] = jaccard(new_communities_list, real_communities_list)
    evals["graph_sensitivity"] = graph_sensitivity(real_communities_list, new_communities_list)
    evals["graph_accuracy"] = graph_accuracy(real_communities_list, new_communities_list)
    return evals


