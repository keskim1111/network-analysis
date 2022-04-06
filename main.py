from consts import evaluation_measures
from helpers import current_time, create_sub_graphs_from_communities
from input_networks import *
from algorithms import *
from output_generator import *

community_file = "C:\\Users\\kimke\\OneDrive\\Documents\\4th year\\semeter B\\Biological networks " \
                  "sadna\\network-analysis\\LFRBenchmark\\Graphs\\1000_0.4_0\\community.dat "
edge_list_path = "C:\\Users\\kimke\OneDrive\\Documents\\4th year\\semeter B\\Biological networks " \
                  "sadna\\network-analysis\\LFRBenchmark\\Graphs\\1000_0.4_2\\network.dat "

n=250
mu=0.1
tau1=3
tau2=1.5
average_degree=4
min_com=15

@timeit
def create_example( is_networkX=False, edge_list_path= None):
    if is_networkX:
        G = create_random_network(n, mu, tau1, tau2, average_degree, min_com)
    else:
        G = create_graph_from_edge_list(edge_list_path)
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


if __name__ == '__main__':
    pass

