import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from algorithms import newman, louvain, algorithms_partition_for_colors
from evaluation import graph_conductance, jaccard, graph_sensitivity, graph_accuracy, modularity
from input_networks import  read_communities_file

RESULTS_FOLDER = "results"
community_file = "C:\\Users\\kimke\\OneDrive\\Documents\\4th year\\semeter B\\Biological networks " \
                 "sadna\\network-analysis\\LFRBenchmark\\Graphs\\1000_0.4_0\\community.dat "


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


def create_output_folder(folder_name, G):
    path = f"{RESULTS_FOLDER}/{folder_name}"
    if not os.path.exists(f"{RESULTS_FOLDER}"):
        os.mkdir(f"{RESULTS_FOLDER}")
    os.mkdir(path)
    with open(f"{RESULTS_FOLDER}/{folder_name}/graph_edges.txt", "w") as f:
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


def run_algos(G):
    algo_dict = {"newman": {"func": newman}, "louvain": {"func": louvain}}
    for algo in algo_dict.keys():
        partition = algo_dict[algo]["func"](G)
        algo_dict[algo]["partition"] = partition
    return algo_dict


def generate_outputs(G, algo_dict, is_networkx=False, real_communities_path=None):
    data = []
    index = []
    if is_networkx:
        real_partition = [list(G.nodes[v]["community"]) for v in G]
    else:
        real_partition = read_communities_file(real_communities_path)
    for algo in algo_dict.keys():
        partition = algo_dict[algo]["partition"]
        res = []
        index.append(algo)
        res.append(modularity(G, partition))
        res.append(graph_conductance(G, partition))
        res.append(jaccard(partition, real_partition))
        res.append(graph_sensitivity(real_partition, partition))
        res.append(graph_accuracy(real_partition, partition))
        data.append(res)
    return data, index