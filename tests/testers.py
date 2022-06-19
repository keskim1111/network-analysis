import random
from pprint import pprint

import networkx as nx
from algorithms.ilp_max_mod_union import ILP
from algorithms.ilp_split_community.our_version import Newman_ILP
from output_generator import generate_outputs_for_community_list


def create_clique_graph(num_cliques=3, min_nodes_in_clique=3, max_nodes_in_clique=12):
    G = nx.Graph()
    communities = []
    for i in range(num_cliques):
        num_nodes_in_clique = random.randint(min_nodes_in_clique, max_nodes_in_clique-1)
        node_range = range(max_nodes_in_clique*i, max_nodes_in_clique*(i+1)-1)
        nodes_in_clique = random.sample(node_range, num_nodes_in_clique)
        communities.append(nodes_in_clique)
        for node_range_1 in range(len(nodes_in_clique)):  # add all possible edges between nodes in clique
            for node_range_2 in range(node_range_1):
                G.add_edge(nodes_in_clique[node_range_1], nodes_in_clique[node_range_2])
    return G, communities


def test_ilp_single(num_cliques, min_nodes_in_clique, max_nodes_in_clique):
    G, real_com = create_clique_graph(num_cliques, min_nodes_in_clique, max_nodes_in_clique)
    ilp = ILP(G, list(G.nodes))
    eval_dict = generate_outputs_for_community_list(G, real_com, ilp.communities)
    print(eval_dict)
    assert eval_dict["modularity - real"] == eval_dict["modularity - algo"], "Modularities should be equal"
    assert eval_dict["num communities - real"] == eval_dict["num communities - algo"], "Number of communities should be equal"
    assert eval_dict["jaccard"] == 1
    assert eval_dict["graph_conductance"] == 1
    assert eval_dict["graph_sensitivity"] == 1
    assert eval_dict["graph_accuracy"] == 1
    nx.draw(G)
    pass

def test_ilp_single_ilp_split(num_cliques, min_nodes_in_clique, max_nodes_in_clique):
    G, real_com = create_clique_graph(num_cliques, min_nodes_in_clique, max_nodes_in_clique)
    ilp = Newman_ILP(G)
    eval_dict = generate_outputs_for_community_list(G, real_com, ilp.communities)
    pprint(eval_dict)
    nx.draw(G)
    pass

def test_ilp_multi():
    for i in range(2, 10):
        test_ilp_single(num_cliques=i, min_nodes_in_clique=5, max_nodes_in_clique=20)
        print(f'==================test_ilp_single on {i} cliques passed===============')
    print(f'test_ilp_multi passed')


if __name__ == "__main__":
    test_ilp_single_ilp_split(num_cliques=2, min_nodes_in_clique=50, max_nodes_in_clique=100)
