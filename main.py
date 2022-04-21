from binary_files import create_binary_network_file, read_binary_network_output
from consts import evaluation_measures, yeast_path
from helpers import current_time, create_sub_graphs_from_communities
from input_networks import *
from algorithms import *
from output_generator import *
from output_generator import generate_outputs_for_community_list
import pickle
from helpers import init_results_folder


@timeit
def create_example( is_networkX=False, edge_list_path= None):
    n = 1000
    mu = 0.1
    tau1 = 3
    tau2 = 1.5
    average_degree = 5
    min_com = 6
    if is_networkX:
        G = create_random_network(n, mu, tau1, tau2, average_degree, min_com)
    else:
        G = create_graph_from_edge_file(edge_list_path)
    print(G)
    algo_dict_partition = run_algos(G)
    data, index = generate_outputs(G, algo_dict_partition, community_file)
    df = create_df(data, evaluation_measures, index)
    params_dict = {"n": n, "original modularity": modularity(G,{frozenset(G.nodes[v]["community"]) for v in G})}
    directory = f"output_{current_time()}"
    path = create_output_folder(directory, G)
    create_pdf(df, f"{path}\\results.pdf", params_dict)
    print(f"Output file created at {path}")
    try:
        create_visual_graphs(G, algo_dict_partition, path)
    except AttributeError:
        print(f"There was an Exception with creating visual_graphs:\n {AttributeError} ")


# Before running neumann C code - creating graph from LFR benchmark networkx
def init_graph_and_folders(params_dict, curr_res_path):

    n = params_dict["n"]
    max_degree = int(n / 10)
    max_community = int(n / 10)

    G = LFR_benchmark_graph(
        n=n, tau1=params_dict["tau1"], tau2=params_dict["tau2"], mu=params_dict["mu"], average_degree=params_dict["average_degree"],
        min_community=params_dict["minimum_community"], max_degree=max_degree, max_community=max_community
    )

    real_communities = {frozenset(G.nodes[v]["community"]) for v in G}
    real_modularity = nx.algorithms.community.modularity(G, real_communities)
    print(f'real_modularity: {real_modularity}')
    binary_network = create_binary_network_file(G, curr_res_path, title=os.path.basename(curr_res_path))

    # saving results for future use
    with open(os.path.join(curr_res_path, "edges.list"), "wb") as f:
        pickle.dump(G.edges, f)
    with open(os.path.join(curr_res_path, "real_communities.dict"), "wb") as f:
        pickle.dump(real_communities, f)
    with open(os.path.join(curr_res_path, "params.dict"), "wb") as f:
        pickle.dump(params_dict, f)
    print(f'saved results in {curr_res_path}')

    return real_communities


def init_graph_and_folder_yeast(res_path):
    with open(os.path.join(yeast_path, "edges.list"), "rb") as f:
        edges_list = pickle.load(f)
    with open(os.path.join(yeast_path, "clusters.list"), "rb") as f:
        real_communities = pickle.load(f)

    G = create_graph_from_edge_list(edges_list)
    real_modularity = nx.algorithms.community.modularity(G, real_communities)
    print(f'real_modularity: {real_modularity}')
    binary_network = create_binary_network_file(G, res_path, title=os.path.basename(res_path))

    # saving results for future use
    with open(os.path.join(res_path, "edges.list"), "wb") as f:
        pickle.dump(G.edges, f)
    with open(os.path.join(res_path, "real_communities.dict"), "wb") as f:
        pickle.dump(real_communities, f)

    print(f'saved results in {res_path}')
    return real_communities

# After running Neumann C code
def run_ilp_on_neuman_output(curr_res_path):
    with open(os.path.join(curr_res_path, "edges.list"), "rb") as f:
        edges_list = pickle.load(f)

    G = create_graph_from_edge_list(edges_list)

    neuman_communities = read_binary_network_output(os.path.join(curr_res_path, f'lp-{os.path.basename(curr_res_path)}-graph.out'))

    sub_graphs = create_sub_graphs_from_communities(G, neuman_communities)
    # run ilp on each communities to continue dividing the communities
    all_communities = []
    for i in range(len(sub_graphs)): # TODO: in the future we can try to run this parallel
        g = sub_graphs[i]
        print(f'------------ {i}/{len(sub_graphs)-1}: starting to run ilp on {g.number_of_nodes()} nodes ----------')
        ilp_obj = ILP(g, is_networx_graph=True)
        curr_communities = ilp_obj.communities
        all_communities += curr_communities
    print(f'finished running ilp')

    # save results
    print(f'saving neuman-ilp results')
    with open(os.path.join(curr_res_path, "neuman_ilp_communities.list"), "wb") as f:
        pickle.dump(all_communities, f)

    return all_communities


def compare_algorithms(res_path):
    with open(os.path.join(res_path, "edges.list"), "rb") as f:
        edges_list = pickle.load(f)

    G = create_graph_from_edge_list(edges_list)

    # getting original communities results from neuman orpaz
    neuman_orpaz_original_communties = read_binary_network_output(os.path.join(res_path, f'original-{os.path.basename(res_path)}-graph.out'))

    # with open(os.path.join(res_path, "neuman_ilp_communities.list"), "rb") as f:
    #     neuman_ilp_communities = pickle.load(f)
    with open(os.path.join(res_path, "real_communities.dict"), "rb") as f:
        real_communities = pickle.load(f)

    real_modularity = nx.algorithms.community.modularity(G, real_communities)
    print(f'real_modularity: {real_modularity}')

    networkx_neuman_communities = newman(G)
    networkx_louvain_communities = louvain(G)

    neuman_eval = generate_outputs_for_community_list(G, real_communities, networkx_neuman_communities)
    louvain_eval = generate_outputs_for_community_list(G, real_communities, networkx_louvain_communities)
    # neuman_ilp_eval = generate_outputs_for_community_list(G, real_communities, neuman_ilp_communities)
    neuman_orpaz_eval = generate_outputs_for_community_list(G, real_communities, neuman_orpaz_original_communties)

    print(f'neuman_eval: {neuman_eval}')
    print(f'louvain_eval: {louvain_eval}')
    # print(f'neuman_ilp_eval: {neuman_ilp_eval}')
    print(f'neuman_orpaz_eval: {neuman_orpaz_eval}')


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
    compare_algorithms(existing_res_path)



"""
idea: there are some subgraphs that ilp takes long to finish. run orpaz-neuman partially, 
but also save the final result. Then - if there is a subgraph that ilp runs for longer
than X minutes - stop the run for this subgraph and put the neuman result instead
Another option is - if it runs too long - then just add that full subgraph as 1 community and dont continue to divide it
"""