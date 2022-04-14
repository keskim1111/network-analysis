from binary_files import create_binary_network_file, read_binary_network_output
from consts import evaluation_measures
from helpers import current_time, create_sub_graphs_from_communities
from input_networks import *
from algorithms import *
from output_generator import *
from output_generator import generate_outputs_for_community_list
import pickle
from consts import RESULTS_FOLDER

community_file = "C:\\Users\\kimke\\OneDrive\\Documents\\4th year\\semeter B\\Biological networks " \
                  "sadna\\network-analysis\\LFRBenchmark\\Graphs\\1000_0.4_0\\community.dat "
edge_list_path = "C:\\Users\\kimke\OneDrive\\Documents\\4th year\\semeter B\\Biological networks " \
                  "sadna\\network-analysis\\LFRBenchmark\\Graphs\\1000_0.4_2\\network.dat "

n=1000
mu=0.1
tau1=3
tau2=1.5
average_degree=5
min_com=6


@timeit
def create_example( is_networkX=False, edge_list_path= None):
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


def init_current_results_folder():
    curr_res_path = os.path.join(RESULTS_FOLDER, f"{current_time()}")
    os.mkdir(curr_res_path)
    return curr_res_path


# Before running neumann C code
def preprocess(params_dict, curr_res_path):

    # creating graph from LFR benchmark networkx
    G = create_random_network(n = params_dict["n"], mu = params_dict["mu"], tau1=params_dict["tau1"], tau2=params_dict["tau2"], average_degree=params_dict["average_degree"], min_community=params_dict["min_com"])
    #os.mkdir(curr_res_path)

    real_communities = {frozenset(G.nodes[v]["community"]) for v in G}
    real_modularity = nx.algorithms.community.modularity(G, real_communities)
    print(f'real_modularity: {real_modularity}')
    binary_network = create_binary_network_file(G, curr_res_path, title=os.path.basename(curr_res_path))

    # run this line after running binary_network in neumann code
    #TODO: orpaz code doesnt seem to stop in LP_CRITICAL (outputs communities that are less than LP_CRITICAL - check if this is an issue with read binary or with orpaz code [printouts])
    #neuman_communities = read_binary_network_output(os.path.join(curr_res_path, "bin-graph.out"))

    #sub_graphs = create_sub_graphs_from_communities(G, neuman_communities)
    # run ilp on each communities to continue dividing the communities
    #for g in sub_graphs:
        # mapping of the nodes and edges in order to run ilp
        #pass

    # saving results for future use
    with open(os.path.join(curr_res_path, "edges.list"), "wb") as f:
        pickle.dump(G.edges, f)
    with open(os.path.join(curr_res_path, "real_communities.dict"), "wb") as f:
        pickle.dump(real_communities, f)
    with open(os.path.join(curr_res_path, "params.dict"), "wb") as f:
        pickle.dump(params_dict, f)
    print(f'saved results in {curr_res_path}')

    return real_communities


# After running Neumann C code
def run_ilp_on_neuman_output(G, curr_res_path):
    # run this line after running binary_network in neumann code
    # TODO: orpaz code doesnt seem to stop in LP_CRITICAL (outputs communities that are less than LP_CRITICAL - check if this is an issue with read binary or with orpaz code [printouts])
    neuman_communities = read_binary_network_output(os.path.join(curr_res_path, f'{os.path.basename(curr_res_path)}-graph.out'))

    sub_graphs = create_sub_graphs_from_communities(G, neuman_communities)
    # run ilp on each communities to continue dividing the communities
    all_communities = []
    for i in range(len(sub_graphs)): # TODO: in the future we can try to run this parallel
        g = sub_graphs[i]
        print(f'------------ {i}/{len(sub_graphs)}: starting to run ilp on {g.number_of_nodes()} nodes ----------')
        ilp_obj = ILP(g, is_networx_graph=True)
        curr_communities = ilp_obj.communities
        all_communities += curr_communities
        print(f'finished running ilp')
    return all_communities


if __name__ == '__main__':
    # curr_res_path = init_current_results_folder()
    # params_dict = {"n": 1000, "mu": 0.1, "tau1": 3, "tau2": 1.5, "average_degree": 5, "min_com": 6}
    # real_communities = preprocess(params_dict, curr_res_path) # creates folder with binary input graph, edges list, real partition

    # if interested to load from exisiting folder
    curr_res_path = os.path.join(RESULTS_FOLDER, "14-04-2022--17-45-04")
    with open(os.path.join(curr_res_path, "edges.list"), "rb") as f:
        edges_list = pickle.load(f)

    G = create_graph_from_edge_list(edges_list)

    neuman_ilp_communities = run_ilp_on_neuman_output(G, curr_res_path)

    # save results
    with open(os.path.join(curr_res_path, "neuman_ilp_communities.list"), "wb") as f:
        pickle.dump(neuman_ilp_communities, f)

    with open(os.path.join(curr_res_path, "real_communities.dict"), "wb") as f:
        real_communities = pickle.load(f)

    eval_results = generate_outputs_for_community_list(G, real_communities, neuman_ilp_communities)
    print(eval_results)