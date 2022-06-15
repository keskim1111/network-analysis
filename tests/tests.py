import os
from timeit import default_timer as timer

from pprint import pprint

from algorithms.Neumann import get_neumann_communities
from algorithms.modified_louvain import modified_louvain_communities
from consts import FOLDER2FLOW_RESULTS
from flow import NetworkObj, RunParamInfo, run_ilp_on_louvain, create_outputs
from helpers import current_time
from logger import setup_logger
import  logging
from algorithms.algorithms import louvain, newman
from algorithms.ilp import ILP
from binary_files import read_binary_network_output
from input_networks import create_random_network, create_graph_from_edge_file, read_communities_file
from output_generator import generate_outputs_for_community_list, save_and_eval
import os.path
import  networkx as nx
in_path = "g.in"
out_path = "g.out"
import statistics

def test_ilp_vs_louvain_small_graph(n=30, min_community=5, max_degree=10, max_community=20, average_degree=2,mu=0.4):
    G = create_random_network(n=n, min_community=min_community, max_degree=max_degree, max_community=max_community, average_degree=average_degree,mu=mu)
    print(G)
    real_communities_sets = {frozenset(G.nodes[v]["community"]) for v in G}
    real_communities = [list(c) for c in real_communities_sets]

    nodes_list = list(G.nodes)
    ilp_obj = ILP(G, nodes_list,TimeLimit=60*5)
    print(ilp_obj.communities)
    louvain_communities = louvain(G)
    dict_louvain = generate_outputs_for_community_list(G, real_communities,louvain_communities,"Louvain")
    dict_ilp = generate_outputs_for_community_list(G,real_communities,ilp_obj.communities,"ILP")
    print("-------------Lovaun------------")
    pprint(dict_louvain)
    print("-------------ILP------------")
    pprint(dict_ilp)
    return  dict_ilp, dict_louvain


def run():
    mu = 0.1
    tau1 = 3
    tau2 = 1.5
    average_degree = 5
    min_com = 20
    for i in range(1, 11):
        n = i * 1000
        G = create_random_network(n, mu, tau1, tau2, average_degree, min_com)
        print(f"run louvain with n {n}")
        com = louvain(G)
        print(f"len of com is {len(com)}")
        print(f"run newman with n {n}")
        com = newman(G)
        print(f"len of com is {len(com)}")


def read_neuman_binary_files_and_print_evaluations(neuman_res_path, original_res_path):
    for file in os.listdir(neuman_res_path):
        if file.endswith("out"):
            neuman_communities = read_binary_network_output(os.path.join(neuman_res_path, file))
            for group in neuman_communities:
                for i in range(len(group)):
                    group[i] += 1
            original_communities = read_communities_file(
                os.path.join(original_res_path, file.split("-graph.out")[0], "community.dat"))
            G = create_graph_from_edge_file(os.path.join(original_res_path, file.split("-graph.out")[0], "network.dat"))
            neuman_eval = generate_outputs_for_community_list(G, original_communities, neuman_communities)
            print(f'{file}: {neuman_eval}')

def create_files_from_networkX_graph(n, mu, graphs_folder):
    # create folder with files
    input_network_name = f"{n}_{mu}-{current_time()}"
    G = create_random_network(n=50, min_community=10, max_degree=20, max_community=20, average_degree=6,mu=mu)
    logging.info(f"created Graph {G}")
    curr_folder_dir = os.path.join(graphs_folder, f"{input_network_name}")
    logging.info(f"Folder of graph is:\n {curr_folder_dir}")
    if not os.path.isdir(curr_folder_dir):
        os.mkdir(curr_folder_dir)
    fh = open(os.path.join(graphs_folder, f"{input_network_name}", "network.dat"), "wb")
    nx.write_edgelist(G, fh,data=False)
    real_communities_sets = {frozenset(G.nodes[v]["community"]) for v in G}
    real_communities = [list(c) for c in real_communities_sets]
    with open(os.path.join(graphs_folder, f"{input_network_name}", "community.dat"), "a") as f:
        cnt = 0
        for i in range(len(real_communities)):
            for j_node in range(len(real_communities[i])):
                f.write(f"{real_communities[i][j_node]}\t{cnt}\n")
            cnt+=1
    logging.info(f"Created graph at {input_network_name}")
    return input_network_name

def one_comparison_run(input_network_folder, path2curr_date_folder):
    # define logger output ##############
    setup_logger(os.path.join(path2curr_date_folder, input_network_folder), log_to_file=True)
    eval_results_per_network = []  # Save all final results in this list (for creating df later)
    logging.info(f'Starting to run algos on input_network_folder= {input_network_folder}')
    network_obj = NetworkObj(path2curr_date_folder, input_network_folder, is_shanis_file=False)


    logging.info(f'===================== Running: Neumann C =======================')
    start = timer()
    neumann_communities = get_neumann_communities(network_obj.save_directory_path, network_obj.network_name,
                                                  network_obj.binary_input_fp, is_shani=False)
    end = timer()
    save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                  network_obj.real_communities,
                  new_communities=neumann_communities, algo="Newman", time=end - start)

    logging.info(f'===================== Running: Louvain networkx =======================')
    start = timer()
    louvain_communities = louvain(network_obj.G)
    end = timer()
    save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                  network_obj.real_communities,
                  new_communities=louvain_communities, algo="Louvain", time=end - start)

    logging.info(f'===================== Running: ILP =======================')
    start = timer()
    nodes_list = list(network_obj.G.nodes)
    ilp_obj = ILP(network_obj.G, nodes_list)
    end = timer()
    save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                  network_obj.real_communities,
                  new_communities=ilp_obj.communities, algo="ILP", time=end - start)

    # outputs
    create_outputs(input_network_folder, eval_results_per_network, network_obj)


def results_folder(init_path, folder_name=""):
    if not os.path.isdir(init_path):
        os.mkdir(init_path)
    if len(folder_name) == 0:  # Create new folder according to current date
        curr_res_path = os.path.join(init_path)
    else:  # Create new folder according to folder_name
        curr_res_path = os.path.join(init_path, folder_name)
    if not os.path.isdir(curr_res_path):
        os.mkdir(curr_res_path)
    return os.path.join(os.getcwd(), curr_res_path)

def run():
    # read_neuman_binary_files_and_print_evaluations( r"C:\Users\kimke\OneDrive\Documents\4th year\semeter
    setup_logger()

    cnt_mod = 0
    cnt_jac = 0
    n = 100
    N = 0
    sum_louvain_mod =0
    sum_ilp_mod =0
    sum_louvain_jac =0
    sum_ilp_jac =0
    for i in range(n):
        # dict_ilp, dict_louvain = test_ilp_vs_louvain_small_graph(n=30, min_community=5, max_degree=10, max_community=20, average_degree=2)
        try:
            dict_ilp, dict_louvain = test_ilp_vs_louvain_small_graph(n=50, min_community=10, max_degree=20, max_community=20, average_degree=6)
            if dict_ilp['modularity - algo'] > dict_louvain['modularity - algo']:
                print(f"ILP won in the {i}th iteration")
                cnt_mod += 1
            if dict_ilp['jaccard'] > dict_louvain['jaccard']:
                cnt_jac +=1
            sum_louvain_mod += dict_louvain['modularity - algo']
            sum_ilp_mod += dict_ilp['modularity - algo']
            sum_louvain_jac += dict_louvain['jaccard']
            sum_ilp_jac += dict_ilp['jaccard']
            N+=1
        except Exception as e:
            print(f"{e}")
            continue
    print(f"----------modularity---------------------")
    print(f"ILP won in rate cnt_mod/N: {cnt_mod / N}")
    print(f"cnt is {cnt_mod}")
    print(f"N is {N}")
    print(f"Louvain Avg is {sum_louvain_mod/N}")
    print(f"ILP Avg is {sum_ilp_mod/N}")
    print(f"----------jaccard---------------------")
    print(f"ILP won in rate cnt_jac/N: {cnt_jac / N}")
    print(f"cnt is {cnt_jac}")
    print(f"N is {N}")
    print(f"Louvain Avg is {sum_louvain_jac/N}")
    print(f"ILP Avg is {sum_ilp_jac/N}")
    test_ilp_vs_louvain_small_graph(n=50, min_community=10, max_degree=20, max_community=20, average_degree=6)
    # test_ilp_vs_louvain_small_graph(n=100, min_community=20, max_degree=40, max_community=40, average_degree=10)

def run2(n):
    # read_neuman_binary_files_and_print_evaluations( r"C:\Users\kimke\OneDrive\Documents\4th year\semeter
    print(f"-----------Running {n} times-----------------")
    setup_logger()
    ilp =[]
    louvain =[]
    for i in range(n):
        # dict_ilp, dict_louvain = test_ilp_vs_louvain_small_graph(n=30, min_community=5, max_degree=10, max_community=20, average_degree=2)
        try:
            dict_ilp, dict_louvain = test_ilp_vs_louvain_small_graph(n=50, min_community=10, max_degree=20, max_community=20, average_degree=6,mu=0.5)
            print((f"Iteration {i}"))
            print(dict_ilp)
            ilp.append(dict_ilp)
            louvain.append(dict_louvain)
        except Exception as e:
            print(f"{e}")
            continue
    return ilp,louvain

def multi_comparison_run(n,num_of_runs):
    path2curr_date_folder = results_folder(FOLDER2FLOW_RESULTS) # results
    for mu in [0.2,0.4,0.5,0.6]:
        for i in range(num_of_runs):
            try:
                print(f"Num iteration {i}\n params: n-{n},mu -{mu}")
                input_path = create_files_from_networkX_graph(n, mu, r"C:\Users\kimke\OneDrive\Documents\4th_year\semeter_B\Biological_networks_sadna\network-analysis\Benchmark\Graphs")
                one_comparison_run(input_path, path2curr_date_folder)
            except Exception as e:
                logging.error(e)
                continue


if __name__ == '__main__':
    multi_comparison_run(50, 50)
    #works
    # path2curr_date_folder = results_folder(FOLDER2FLOW_RESULTS) # results
    # input_path = create_files_from_networkX_graph(50, 0.2, r"C:\Users\kimke\OneDrive\Documents\4th_year\semeter_B\Biological_networks_sadna\network-analysis\Benchmark\Graphs")
    # # input_path = "50_0.4"
    # one_comparison_run(input_path, path2curr_date_folder)

    # ilp, louvain = run2(50)
    # louvain_mod_avg = statistics.mean([d['modularity - algo'] for d in louvain])
    # louvain_jaccard_avg = statistics.mean([d['jaccard'] for d in louvain])
    #
    # louvain_mod_std = statistics.stdev([d['modularity - algo'] for d in louvain])
    # louvain_jaccard_std = statistics.stdev([d['jaccard'] for d in louvain])
    #
    #
    # ilp_mod_avg = statistics.mean([d['modularity - algo'] for d in ilp])
    # ilp_jaccard_avg = statistics.mean([d['jaccard'] for d in ilp])
    #
    # ilp_mod_std = statistics.stdev([d['modularity - algo'] for d in ilp])
    # ilp_jaccard_std = statistics.stdev([d['jaccard'] for d in ilp])
    #
    # print(f"----ilp_mod_avg----\n{ilp_mod_avg}")
    # print(f"----ilp_mod_std----\n{ilp_mod_std}")
    #
    # print(f"----louvain_mod_avg----\n{louvain_mod_avg}")
    # print(f"----louvain_mod_std----\n{louvain_mod_std}")
    #
    # print(f"----ilp_jaccard_avg----\n{ilp_jaccard_avg}")
    # print(f"----ilp_jaccard_std----\n{ilp_jaccard_std}")
    #
    # print(f"----louvain_jaccard_avg----\n{louvain_jaccard_avg}")
    # print(f"----louvain_jaccard_std----\n{louvain_jaccard_std}")



