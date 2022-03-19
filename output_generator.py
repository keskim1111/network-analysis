import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import scipy.sparse.csgraph


def create_visual_graph(G, partition, output):
    pos = nx.spring_layout(G)
    cmap = cm.get_cmap('viridis', max(partition.values()) + 1)
    nodes = nx.draw_networkx_nodes(G, pos, partition.keys(), node_size=10, cmap=cmap,
                                   node_color=list(partition.values()))
    edges = nx.draw_networkx_edges(G, pos)
    plt.savefig(f"{output}.png", dpi=120)
