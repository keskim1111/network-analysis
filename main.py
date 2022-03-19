from input_networks import *
from algorithms import *
from output_generator import *
import networkx as nx


possible_mus = [0.4, 0.5, 0.6]
possible_ns = [1000, 10000]
msg = "The modularity result of the Algorithm is: "
def create_example():
    G = create_random_network(250, 0.1, 3, 1.5, 5, 20)
    communities_newman = newman(G)
    newman_partition = algorithms_partition_for_colors(communities_newman)

    print(f"Newman - {msg}{nx.algorithms.community.modularity(G,communities_newman)}")
    communities_louvain = louvain(G)
    louvain_partition = algorithms_partition_for_colors(communities_louvain)
    print(f"Louvain - {msg}{nx.algorithms.community.modularity(G,communities_louvain)} with {len(communities_louvain)} "
          f"communities and {sum(len(sett) for sett in communities_louvain)} items")

    real_communities = {frozenset(G.nodes[v]["community"]) for v in G}
    real_partition = algorithms_partition_for_colors(real_communities)
    print(f"Real - {msg}{nx.algorithms.community.modularity(G,real_communities)} with {len(real_communities)} "
          f"communities and {sum(len(sett) for sett in real_communities)} items")

    #creates graphs
    create_visual_graph(G, real_partition, "real")
    create_visual_graph(G, newman_partition, "newman_partition")
    create_visual_graph(G, louvain_partition, "louvain_partition")


create_example()



