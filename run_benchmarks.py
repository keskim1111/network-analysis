from networkx.generators.community import LFR_benchmark_graph
import networkx as nx
import community as community_louvain
import matplotlib.pyplot as plt
import matplotlib.cm as cm

#
# # define the graph
# edge = [(1,2),(1,3),(1,4),(1,5),(1,6),(2,7),(2,8),(2,9)]
# G = nx.Graph()
# G.add_edges_from(edge)
# retrun partition as a dict
# partition = community_louvain.best_partition(G)
# print(partition)
# visualization
# pos = nx.spring_layout(G)
# cmap = cm.get_cmap('viridis', max(partition.values()) + 1)
# nx.draw_networkx_nodes(G, pos, partition.keys(), node_size=100,cmap=cmap, node_color=list(partition.values()))
# nx.draw_networkx_edges(G, pos, alpha=0.5)
# plt.show()



#
n = 250
tau1 = 5
tau2 = 1.5
mu = 0.1
G = LFR_benchmark_graph(
    n, tau1, tau2, mu, average_degree=5, min_community=20, seed=10
)
partition = community_louvain.best_partition(G)

communities = {frozenset(G.nodes[v]["community"]) for v in G}
partition = dict()
col = 0
for com in communities:
    for node in com:
        partition[node] = col
    col += 1


# visualization
pos = nx.spring_layout(G)
cmap = cm.get_cmap('viridis', max(partition.values()) + 1)
nx.draw_networkx_nodes(G, pos, partition.keys(), node_size=10,cmap=cmap, node_color=list(partition.values()))
nx.draw_networkx_edges(G, pos, alpha=0.5)
plt.show()

"""
- understand benchmark parameters function
- add function that calculates modularity of benchmark graph https://github.com/taynaud/python-louvain
- compare modularity to louvain and neuman
- create function that summarizes results when running examples
- measure time
- 

"""

# pos = nx.spring_layout(G)
# #cmap = cm.get_cmap('viridis', max(partition.values()) + 1)
# nx.draw_networkx_nodes(G, pos, node_size=100)
# nx.draw_networkx_edges(G, pos, alpha=0.5)
# plt.show()
