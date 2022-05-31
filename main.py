from consts import evaluation_measures
from helpers import current_time
from input_networks import *
from output_generator import *
from algorithms.ilp import run_ilp_on_neuman_output


# def init_graph_and_folder_yeast(res_path):
#     with open(os.path.join(yeast_path, "edges.list"), "rb") as f:
#         edges_list = pickle.load(f)
#     with open(os.path.join(yeast_path, "clusters.list"), "rb") as f:
#         real_communities = pickle.load(f)
#
#     G = create_graph_from_edge_list(edges_list)
#     real_modularity = nx.algorithms.community.modularity(G, real_communities)
#     print(f'real_modularity: {real_modularity}')
#     binary_network = create_binary_network_file(G, res_path, title=os.path.basename(res_path))
#
#     # saving results for future use
#     with open(os.path.join(res_path, "edges.list"), "wb") as f:
#         pickle.dump(G.edges, f)
#     with open(os.path.join(res_path, "real_communities.dict"), "wb") as f:
#         pickle.dump(real_communities, f)
#
#     print(f'saved results in {res_path}')
#     return real_communities


# def compare_algorithms(res_path):
#     with open(os.path.join(res_path, "edges.list"), "rb") as f:
#         edges_list = pickle.load(f)
#
#     G = create_graph_from_edge_list(edges_list)
#
#     # getting original communities results from neuman orpaz
#     neuman_orpaz_original_communties = read_binary_network_output(os.path.join(res_path, f'original-{os.path.basename(res_path)}-graph.out'))
#
#     # with open(os.path.join(res_path, "neuman_ilp_communities.list"), "rb") as f:
#     #     neuman_ilp_communities = pickle.load(f)
#     with open(os.path.join(res_path, "real_communities.dict"), "rb") as f:
#         real_communities = pickle.load(f)
#
#     real_modularity = nx.algorithms.community.modularity(G, real_communities)
#     print(f'real_modularity: {real_modularity}')
#
#     networkx_neuman_communities = newman(G)
#     networkx_louvain_communities = louvain(G)
#
#     neuman_eval = generate_outputs_for_community_list(G, real_communities, networkx_neuman_communities)
#     louvain_eval = generate_outputs_for_community_list(G, real_communities, networkx_louvain_communities)
#     # neuman_ilp_eval = generate_outputs_for_community_list(G, real_communities, neuman_ilp_communities)
#     neuman_orpaz_eval = generate_outputs_for_community_list(G, real_communities, neuman_orpaz_original_communties)
#
#     print(f'neuman_eval: {neuman_eval}')
#     print(f'louvain_eval: {louvain_eval}')
#     # print(f'neuman_ilp_eval: {neuman_ilp_eval}')
#     print(f'neuman_orpaz_eval: {neuman_orpaz_eval}')


if __name__ == '__main__':
    # new_res_path = init_results_folder()
    # # real_communities = init_graph_and_folder_yeast(new_res_path)
    #
    # params_dict = {"n": 1000, "mu": 0.1, "tau1": 2, "tau2": 1.1, "average_degree": 25, "minimum_community": 50}
    # real_communities = init_graph_and_folders(params_dict, new_res_path)

    # run this after running neuman code on network (original and ilp version)
    existing_res_path = os.path.join(RESULTS_FOLDER, "17-04-2022--17-53-03")
    neuman_ilp_communities = run_ilp_on_neuman_output(existing_res_path)

    print(f'evaluating results')
    # add relevant function here
    # compare_algorithms(existing_res_path)



"""
idea: there are some subgraphs that ilp takes long to finish. run orpaz-neuman partially, 
but also save the final result. Then - if there is a subgraph that ilp runs for longer
than X minutes - stop the run for this subgraph and put the neuman result instead
Another option is - if it runs too long - then just add that full subgraph as 1 community and dont continue to divide it
"""