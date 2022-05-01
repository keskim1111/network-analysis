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

@timeit
def run_algo_on_neumann_results(network_obj, neumann_communities, run_ilp=False, run_louvain=False):
    neumann_sub_graphs = create_sub_graphs_from_communities(network_obj.G, neumann_communities)
    neumann_and_algo_communities = []

    count_louvain = 0
    count_ilp = 0
    count_no_divide = 0
    for i in range(len(neumann_sub_graphs)):
        g = neumann_sub_graphs[i]
        g_size = len(g.nodes)

        print(f'============== Iteration {i+1}/{len(neumann_sub_graphs)}, subgraph size = {g_size} ================')

        if run_ilp:
            try:
                print(f'============Trying to run ILP')
                ilp_obj = ILP(g, is_networkx_graph=True)
                curr_communities = ilp_obj.communities
                count_ilp += 1
            except Exception: # not sure I have to add 60 here
                print(f'passed timeout time')
                if run_louvain: # Run Louvain on graphs that ilp didn't manage
                    count_louvain += 1
                    curr_communities = louvain(g)
                else: # Don't divide subgraph more
                    curr_communities = [
                        list(g.nodes)]  # TODO: check that this is the correct list format (list of list)
                    count_no_divide += 1
        elif (run_louvain and not run_ilp):
            count_louvain += 1
            curr_communities = louvain(g)
        else:
            print("need to choose run_ilp or run_louvain")
            raise Exception
        print(f'Num of curr_communities: {len(curr_communities)}')
        neumann_and_algo_communities += curr_communities

        print(f'count_louvain: {count_louvain}, count_ilp: {count_ilp}, count_no_divide: {count_no_divide}, total: {len(neumann_sub_graphs)}')

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


def multi_run():
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)

    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True):
        print(f'Starting to run algos on input_network_folder= {input_network_folder}')
        evals_list = []

        network_obj = NetworkObj(path2curr_date_folder, input_network_folder)

        print(f'===================== Running: Neumann C =======================')
        # Get evaluations
        neumann_communities = get_neumann_communities(network_obj, lp_critical=1)

        # Saving results to file
        algo = "Neumann"
        com_list = neumann_communities
        _pickle(os.path.join(network_obj.save_folder, f'{algo}.communities'), object=com_list, is_dump=True)

        # Evaluate results and save to eval_dict
        eval_dict = generate_outputs_for_community_list(network_obj.G, network_obj.real_communities, com_list)
        eval_dict["algo"] = algo
        evals_list.append(eval_dict)

        print(f'===================== Running: Louvain networkx =======================')
        curr_com = louvain(network_obj.G)

        # Saving results to file
        algo = "Louvain"
        com_list = curr_com
        _pickle(os.path.join(network_obj.save_folder, f'{algo}.communities'), object=com_list, is_dump=True)

        # Evaluate results and save to eval_dict
        eval_dict = generate_outputs_for_community_list(network_obj.G, network_obj.real_communities, com_list)
        eval_dict["algo"] = algo
        evals_list.append(eval_dict)

        print(f'===================== Running: Neumann C + Louvain networkx =======================')
        curr_com = run_algo_on_neumann_results(network_obj, neumann_communities, run_louvain=True)

        # Saving results to file
        algo = "Neumann-Louvain"
        com_list = curr_com
        _pickle(os.path.join(network_obj.save_folder, f'{algo}.communities'), object=com_list, is_dump=True)

        # Evaluate results and save to eval_dict
        eval_dict = generate_outputs_for_community_list(network_obj.G, network_obj.real_communities, com_list)
        eval_dict["algo"] = algo
        evals_list.append(eval_dict)

        print(f'===================== Running: Neumann C + Louvain networkx + ILP (according to timeit) =======================')
        lp_critical_list = [50, 100, 150]
        for lp_critical in lp_critical_list:
            print(f'=================== LP_critical={lp_critical} ===============')
            curr_neumann_com = get_neumann_communities(network_obj, lp_critical=lp_critical)

            curr_com = run_algo_on_neumann_results(network_obj, curr_neumann_com, run_ilp=True,
                                                   run_louvain=True)
            # Saving results to file
            algo = f'Neumann-Louvain-ILP-{lp_critical}'
            com_list = curr_com
            _pickle(os.path.join(network_obj.save_folder, f'{algo}.communities'), object=com_list, is_dump=True)

            # Evaluate results and save to eval_dict
            eval_dict = generate_outputs_for_community_list(network_obj.G, network_obj.real_communities, com_list)
            eval_dict["algo"] = algo
            evals_list.append(eval_dict)


            curr_com = run_algo_on_neumann_results(network_obj, curr_neumann_com, run_ilp=True)
            # Saving results to file
            algo = f'Neumann-ILP-{lp_critical}'
            com_list = curr_com
            _pickle(os.path.join(network_obj.save_folder, f'{algo}.communities'), object=com_list, is_dump=True)

            # Evaluate results and save to eval_dict
            eval_dict = generate_outputs_for_community_list(network_obj.G, network_obj.real_communities, com_list)
            eval_dict["algo"] = algo
            evals_list.append(eval_dict)
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
    multi_run()
    # res = _pickle("C://Users//97252//Documents//year_4//sadna//network-analysis//full_flow//01-05-2022--22-35-12//1000_0.6_9//evals.list", is_load=True)
    #
    # df = pd.DataFrame(res)
    # df2 = pd.read_pickle("C://Users//97252//Documents//year_4//sadna//network-analysis//full_flow//01-05-2022--22-35-12//1000_0.6_9//results.df")
    # df2.to_csv("C://Users//97252//Documents//year_4//sadna//network-analysis//full_flow//01-05-2022--22-35-12//1000_0.6_9//results_df.csv")
    # display(df2)
    pass





