import os, os.path, time, subprocess, pickle
import pandas as pd

from algorithms import louvain
from binary_files import read_binary_network_output, create_binary_network_file
from consts import C_CODE, PATH2SHANIS_GRAPHS, FOLDER2FLOW_RESULTS
from input_networks import create_graph_from_edge_file, read_communities_file, create_graph_from_edge_list
from helpers import init_results_folder, timeout, _pickle, timeit, create_sub_graphs_from_communities
from output_generator import generate_outputs_for_community_list
from IPython.display import display
from ilp import ILP



@timeout(120)
def run_cmd(command, run_path):
    os.chdir(run_path)
    print(f"current path = {os.getcwd()}")
    print(f"current cmd running = {command}")
    process = subprocess.Popen(command, shell=True)
    process.communicate()
    errcode = process.returncode
    process.kill()
    process.terminate()


def run_func_after_file_created(file_created_path, func, args):
    '''
    :param file_created_path:
    :param func:
    :param arg: a dict with key as arg name and value
    :return:
    '''
    print(" running run_func_after_file_created")
    while not os.path.exists(file_created_path):
        time.sleep(1)
    if os.path.isfile(file_created_path):
        print(f"file created in {file_created_path}")
        res = func(**args)
        return res
    else:
        raise ValueError("%s isn't a file!" % file_created_path)


def create_data_dict(evals_list):
    """
    :param evals_list: list of eval dictionaries
    :return: data dict for df input
    """
    data_dict = {}
    for eval_dict in evals_list:
        for k, v in eval_dict.items():
            if not data_dict.get(k):
                data_dict[k] = []
            data_dict[k].append(v)
    return data_dict

@timeit
def get_neumann_communities(network_obj, lp_critical=1):
    binary_output_fp = os.path.join(network_obj.save_folder,
                                    f"{network_obj.network_name}_{lp_critical}.out")  # defining path to output file
    command = f".\cluster {network_obj.binary_input_fp} {binary_output_fp} {lp_critical}" # command for neuman C code
    run_cmd(command, C_CODE)
    neumann_communities = run_func_after_file_created(binary_output_fp, read_binary_network_output, {"fileName": binary_output_fp, "is_shani": True})

    return neumann_communities


def calculate_modularity(G, communities: list):
    """
    :param G: networkx graph
    :param communities: list of lists of ints (nodes)
    :return:
    """
    sum_modularity = 0
    for i in range(len(communities)):
        nodes_list = communities[i]
        num_of_nodes = len(nodes_list)
        m = G.number_of_edges()
        adj = G.adj
        cur_modularity = 0 # [sum_ij] (a_ij - (d_i * d_j)/2m)
        for node_range_1 in range(num_of_nodes):
            for node_range_2 in range(node_range_1):  # i < j
                j = nodes_list[node_range_1]
                i = nodes_list[node_range_2]

                if dict(adj[i].items()).get(j) is not None:
                    a_ij = dict(adj[i].items())[j].get("weight", 1)
                else:
                    a_ij = 0

                cur_modularity = a_ij - (G.degree(i) * G.degree(j)) / (2 * m)
        sum_modularity += cur_modularity
    return sum_modularity


@timeit
def run_algo_on_neumann_results(network_obj, neumann_communities, lp_critical):
    neumann_and_algo_communities = []
    # counts = {"count_ilp": 0, "count_no_divide": 0, "count_louvain": 0}
    G = network_obj.G  # Original graph

    for i in range(len(neumann_communities)):
        nodes_list = neumann_communities[i]
        num_nodes = len(nodes_list)

        if num_nodes > lp_critical:  # This community already reached maximal modularity - no need to divide more
            continue

        curr_modularity = calculate_modularity(G, [nodes_list]) # Modularity before dividing more with ILP

        print(f'============== Iteration {i+1}/{len(neumann_communities)}, subgraph size = {num_nodes} ================')

        try: # TODO: Remove this try and exception when timeout is param of Gurobi
            print(f'============Trying to run ILP')
            ilp_obj = ILP(G, nodes_list)
            new_modularity = calculate_modularity(G, ilp_obj.communities)  # TODO: make sure this is equal to ilp_obj.model.ObjVal

            if new_modularity > curr_modularity:
                curr_communities = ilp_obj.communities  # New division
            else:
                curr_communities = [nodes_list]  # Initial division

        except Exception:
            print(f'passed timeout time')
            # Don't divide subgraph more
            curr_communities = [nodes_list]
            # count_no_divide += 1

        print(f'Num of curr_communities: {len(curr_communities)}')
        neumann_and_algo_communities += curr_communities

    return neumann_and_algo_communities


class NetworkObj:
    def __init__(self, main_dp, network_name):
        self.network_name = network_name
        self.save_folder = init_results_folder(main_dp, network_name)
        self.network_dp = os.path.join(PATH2SHANIS_GRAPHS, self.network_name)
        self.real_communities = read_communities_file(os.path.join(self.network_dp, "community.dat"))
        _pickle(os.path.join(self.save_folder, "real.communities"), self.real_communities, is_dump=True)
        self.G = create_graph_from_edge_file(os.path.join(self.network_dp, "network.dat"))  # creating graph object
        self.binary_input_fp = create_binary_network_file(self.G, self.save_folder, title=self.network_name,
                                                     is_shanis_file=True)  # converting network to binary file


def save_and_eval(network_obj, evals_list, algo, com_list):

    _pickle(os.path.join(network_obj.save_folder, f'{algo}.communities'), object=com_list, is_dump=True)

    # Evaluate results and save to eval_dict
    eval_dict = generate_outputs_for_community_list(network_obj.G, network_obj.real_communities, com_list)
    eval_dict["algo"] = algo
    evals_list.append(eval_dict)


def multi_run(lp_critical_list):
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)

    # run on all of shani's networks
    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True):

        print(f'Starting to run algos on input_network_folder= {input_network_folder}')
        evals_list = []  # Save all final results in this list (for creating df later)
        network_obj = NetworkObj(path2curr_date_folder, input_network_folder)

        print(f'===================== Running: Neumann C =======================')
        neumann_communities = get_neumann_communities(network_obj, lp_critical=1)
        save_and_eval(network_obj, evals_list, algo="Neumann", com_list=neumann_communities)

        print(f'===================== Running: Louvain networkx =======================')
        curr_com = louvain(network_obj.G)
        save_and_eval(network_obj, evals_list, algo="Louvain", com_list=curr_com)

        print(f'===================== Running: Neumann C + ILP (according to timeit) =======================')
        for lp_critical in lp_critical_list:
            print(f'=================== LP_critical={lp_critical} ===============')
            curr_neumann_com = get_neumann_communities(network_obj, lp_critical=lp_critical)
            curr_com, counts = run_algo_on_neumann_results(network_obj, curr_neumann_com, run_ilp=True)
            save_and_eval(network_obj, evals_list, algo=f'Neumann-ILP-{lp_critical}', com_list=curr_com)

        _pickle(os.path.join(network_obj.save_folder, 'evals.list'), object=evals_list, is_dump=True)
        print(f'Finished running algos on input_network_folder= {input_network_folder}')

        # Create df per network
        print(f'Creating DF for this network:')
        data_dict = create_data_dict(evals_list)
        df = pd.DataFrame(data_dict)
        df.to_pickle(os.path.join(network_obj.save_folder, "results.df"))
        df.to_csv(os.path.join(network_obj.save_folder, "results_df.csv"))
        # df.read_pickle to read results


if __name__ == '__main__':
    lp_critical_list = [100]
    multi_run(lp_critical_list)
    pass





