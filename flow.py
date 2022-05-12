import os
import pandas as pd
from algorithms import louvain
from binary_files import create_binary_network_file
from consts import PATH2SHANIS_GRAPHS, FOLDER2FLOW_RESULTS
from evaluation import calc_modularity_manual
from input_networks import create_graph_from_edge_file, read_communities_file
from helpers import init_results_folder, timeout, _pickle, timeit
from output_generator import generate_outputs_for_community_list
from IPython.display import display
from ilp import ILP
from Neumann import get_neumann_communities


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


def run_ilp_on_neumann(G, neumann_communities: list, lp_critical: int):
    final_communities = []

    for i in range(len(neumann_communities)):
        nodes_list = neumann_communities[i]
        num_nodes = len(nodes_list)

        print(f'============== Iteration {i+1}/{len(neumann_communities)}, subgraph size = {num_nodes} ================')

        if num_nodes > lp_critical:  # This community already reached maximal modularity - no need to divide more
            print(f'num nodes {num_nodes} > lp_critical {lp_critical}, skipping.')
            curr_communities = [nodes_list]
            final_communities += curr_communities
            continue

        curr_modularity = calc_modularity_manual(G, [nodes_list])  # Modularity before dividing more with ILP
        print(f'curr_modularity: {curr_modularity}')

        try: # TODO: Remove this try and exception when timeout is param of Gurobi
            print(f'============Trying to run ILP')
            ilp_obj = ILP(G, nodes_list)
            new_modularity = calc_modularity_manual(G, ilp_obj.communities)  # TODO: make sure this is equal to ilp_obj.model.ObjVal
            print(f'new_modularity: {new_modularity}')

            if new_modularity > curr_modularity:
                print(f'new_modularity: {new_modularity} larger than curr_modularity: {curr_modularity}. Adding ILP division.')
                curr_communities = ilp_obj.communities  # New division
            else:
                print(f'curr_modularity: {curr_modularity} larger than new_modularity: {new_modularity}')
                curr_communities = [nodes_list]  # Initial division

        except Exception:  # need to make this exception more specific (timeout)
            print(f'passed timeout time, adding community without further division.')
            curr_communities = [nodes_list]  # Don't divide subgraph more

        print(f'Num of curr_communities: {len(curr_communities)}')
        final_communities += curr_communities

    return final_communities


class NetworkObj:
    def __init__(self, main_dp, network_name):
        self.network_name = network_name
        self.save_dp = init_results_folder(main_dp, network_name)
        self.network_dp = os.path.join(PATH2SHANIS_GRAPHS, self.network_name)
        self.real_communities = read_communities_file(os.path.join(self.network_dp, "community.dat"))
        _pickle(os.path.join(self.save_dp, "real.communities"), self.real_communities, is_dump=True)
        self.G = create_graph_from_edge_file(os.path.join(self.network_dp, "network.dat"))  # creating graph object
        self.binary_input_fp = create_binary_network_file(self.G, self.save_dp, title=self.network_name,
                                                     is_shanis_file=True)  # converting network to binary file


# TODO: add run time
def save_and_eval(save_dp, evals_list, G, real_communities, new_communities, algo):
    # Saving communities object to folder
    _pickle(os.path.join(save_dp, f'{algo}.communities'), object=new_communities, is_dump=True)

    # Evaluate results and save to eval_dict
    eval_dict = generate_outputs_for_community_list(G, real_communities, new_communities, algo=algo)
    evals_list.append(eval_dict)


# run on all of shani's networks
def multi_run(lp_critical_list):
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)

    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True):

        print(f'Starting to run algos on input_network_folder= {input_network_folder}')
        eval_results_per_network = []  # Save all final results in this list (for creating df later)
        network_obj = NetworkObj(path2curr_date_folder, input_network_folder)

        print(f'===================== Running: Neumann C =======================')
        neumann_communities = get_neumann_communities(network_obj.save_dp, network_obj.network_name, network_obj.binary_input_fp)
        save_and_eval(network_obj.save_dp, eval_results_per_network, network_obj.G, network_obj.real_communities, new_communities=neumann_communities,  algo="Neumann")

        print(f'===================== Running: Louvain networkx =======================')
        louvain_communities = louvain(network_obj.G)
        save_and_eval(network_obj.save_dp, eval_results_per_network, network_obj.G, network_obj.real_communities, new_communities=louvain_communities, algo="Louvain")

        print(f'===================== Running: Neumann C + ILP (according to timeit) =======================')
        for lp_critical in lp_critical_list:
            print(f'=================== LP_critical={lp_critical} ===============')
            neuman_com_partial_run = get_neumann_communities(network_obj.save_dp, network_obj.network_name, network_obj.binary_input_fp, lp_critical=lp_critical)
            neumann_ilp_com = run_ilp_on_neumann(network_obj.G, neuman_com_partial_run, lp_critical=lp_critical)
            save_and_eval(network_obj.save_dp, eval_results_per_network, network_obj.G, network_obj.real_communities,
                          new_communities=neumann_ilp_com, algo=f'Neumann-ILP-{lp_critical}')

        # Saving evals of this network
        # _pickle(os.path.join(network_obj.save_dp, 'evals.list'), object=eval_results_per_network, is_dump=True)
        print(f'Finished running algos on input_network_folder= {input_network_folder}')

        # Create df per network
        print(f'Creating DF for this network:')
        data_dict = create_data_dict(eval_results_per_network)
        df = pd.DataFrame(data_dict)
        df.to_pickle(os.path.join(network_obj.save_dp, "results.df"))
        df.to_csv(os.path.join(network_obj.save_dp, "results_df.csv"))
        # df.read_pickle to read results


if __name__ == '__main__':
    lp_critical_list = [100]
    multi_run(lp_critical_list)
    pass





