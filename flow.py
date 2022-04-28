import os, os.path, time, subprocess
import pandas as pd

from algorithms import louvain
from binary_files import read_binary_network_output, create_binary_network_file
from consts import C_CODE, PATH2SHANIS_GRAPHS, FOLDER2FLOW_RESULTS
from input_networks import create_graph_from_edge_file, read_communities_file, create_graph_from_edge_list
from helpers import init_results_folder, timeout, _pickle, timeit, create_sub_graphs_from_communities
from output_generator import generate_outputs_for_community_list
from pprint import pprint
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
        for k, v in eval_dict.items:
            if not data_dict.get(k):
                data_dict[k] = []
            data_dict[k].append(v)
    return data_dict


def get_neumann_communities(network_obj, lp_critical=1):
    binary_output_fp = os.path.join(network_obj.save_folder,
                                    f"{network_obj.network_name}_{lp_critical}.out")  # defining path to output file
    command = f".\cluster {network_obj.binary_input_fp} {binary_output_fp} {lp_critical}" # command for neuman C code
    run_cmd(command, C_CODE)
    neumann_communities = run_func_after_file_created(binary_output_fp, read_binary_network_output, {"fileName": binary_output_fp, "is_shani": True})

    return neumann_communities


def run_algo_on_neumann(network_obj, neumann_communities, run_ilp=False, run_louvain=False, max_ilp_size=100):
    neumann_sub_graphs = create_sub_graphs_from_communities(network_obj.G, neumann_communities)
    neumann_and_algo_communities = []

    count_louvain = 0
    count_ilp = 0

    for i in range(len(neumann_sub_graphs)):
        g = neumann_sub_graphs[i]
        g_size = len(g.nodes)
        print(f'============== Iteration {i}, subgraph size = {g_size} ================')

        if run_ilp and g_size<=max_ilp_size: # TODO: add try and except with timeout instead of graph size
            ilp_obj = ILP(g, is_networkx_graph=True)
            curr_communities = ilp_obj.communities
            count_ilp += 1

        elif run_louvain:
            count_louvain += 1
            curr_communities = louvain(g)

        else: # Don't divide group more
            curr_communities = [list(g.nodes)]  # TODO: check that this is the correct list format (list of list)
        print(f'Num of curr_communities: {len(curr_communities)}')
        neumann_and_algo_communities += curr_communities

        print(f'count_louvain: {count_louvain}, count_ilp: {count_ilp}, total: {len(neumann_sub_graphs)}')

    return neumann_and_algo_communities


class NetworkObj:
    def __init__(self, network_name):
        self.network_name = network_name
        self.save_folder = init_results_folder(FOLDER2FLOW_RESULTS)
        self.network_dp = os.path.join(PATH2SHANIS_GRAPHS, self.network_name)
        self.real_communities = read_communities_file(os.path.join(self.network_dp, "community.dat"))
        _pickle(os.path.join(self.save_folder, "real.communities"), self.real_communities, is_dump=True)
        self.G = create_graph_from_edge_file(self.network_dp)  # creating graph object
        self.binary_input_fp = create_binary_network_file(self.G, self.save_folder, title=self.network_name,
                                                     is_shanis_file=True)  # converting network to binary file


def multi_run():
    evals_list = []

    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True):
        network_obj = NetworkObj(input_network_folder)

        algo_communities_dict = {}
        print(f'===================== Running: Neumann C =======================')
        # Get evaluations
        neumann_communities = get_neumann_communities(network_obj, lp_critical=1)
        algo_communities_dict["Neumann"] = neumann_communities

        print(f'===================== Running: Louvain networkx =======================')
        curr_com = louvain(network_obj.G)
        algo_communities_dict["Louvain"] = curr_com

        print(f'===================== Running: Neumann C + Louvain networkx =======================')
        curr_com = run_algo_on_neumann(network_obj, neumann_communities, run_louvain=True)
        algo_communities_dict["Neumann-Louvain"] = curr_com

        print(f'===================== Running: Neumann C + Louvain networkx + ILP (according to timeit) =======================')
        lp_critical_list = [50, 100, 150]
        for lp_critical in lp_critical_list:
            print(f'=================== LP_critical={lp_critical} ===============')
            curr_neumann_com = get_neumann_communities(network_obj, lp_critical=lp_critical)

            curr_com = run_algo_on_neumann(network_obj, curr_neumann_com, run_ilp=True,
                                                                  run_louvain=True) # TODO: add timeout
            algo_communities_dict[f'Neumann-Louvain-ILP-{lp_critical}'] = curr_com

            curr_com = run_algo_on_neumann(network_obj, curr_neumann_com, run_ilp=True) # TODO: add timeout
            algo_communities_dict[f'Neumann-ILP-{lp_critical}'] = curr_com

        print(f'========Saving all results=========')
        for algo, com_list in algo_communities_dict.items():
            # Saving results to file
            _pickle(os.path.join(network_obj.save_folder, f'{algo}.communities'), object=com_list, is_dump=True)

            # Evaluate results and save to eval_dict
            eval_dict = generate_outputs_for_community_list(network_obj.G, network_obj.real_communities, com_list)
            evals_list.append(eval_dict)
            # add network_obj.network_name to evals_list

    data_dict = create_data_dict(evals_list)
    df = pd.DataFrame(data_dict)


if __name__ == '__main__':
    multi_run()
    pass





