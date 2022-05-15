import os
from timeit import default_timer as timer
import pandas as pd
import logging
from algorithms.algorithms import louvain
from binary_files import create_binary_network_file
from consts import PATH2SHANIS_GRAPHS, FOLDER2FLOW_RESULTS
from evaluation import calc_modularity_manual
from input_networks import create_graph_from_edge_file, read_communities_file
from helpers import init_results_folder, _pickle, define_logger, prompt_file
from logger import setup_logger
from output_generator import generate_outputs_for_community_list, save_and_eval
from algorithms.ilp import ILP
from algorithms.Neumann import get_neumann_communities


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


def run_ilp_on_neumann(G, neumann_communities: [list], lp_critical: int, IntFeasTol=float(1e-5),TimeLimit=False):
    final_communities = []
    num_communities_divided_by_ilp = 0
    num_communities_skipped_by_ilp = 0
    for i in range(len(neumann_communities)):
        nodes_list = neumann_communities[i]
        num_nodes = len(nodes_list)
        logging.info(
            f'============== Iteration {i + 1}/{len(neumann_communities)}, subgraph size = {num_nodes} ================')
        if num_nodes > lp_critical:  # This community already reached maximal modularity - no need to divide more
            logging.info(f'num nodes {num_nodes} > lp_critical {lp_critical}, skipping.')
            num_communities_skipped_by_ilp += 1
            curr_communities = [nodes_list]
            final_communities += curr_communities
            continue

        curr_modularity = calc_modularity_manual(G, [nodes_list])  # Modularity before dividing more with ILP
        logging.info(f'Modularity of graph before {i + 1}th ILP iteration: {curr_modularity}')
        sub_graph = G.subgraph(nodes_list)
        try:  # TODO: Remove this try and exception when timeout is param of Gurobi
            logging.info(f'============Trying to run ILP')
            logging.info("complete")
            ilp_obj = ILP(G, nodes_list, IntFeasTol, TimeLimit)
            new_modularity = calc_modularity_manual(G,
                                                    ilp_obj.communities)  # TODO: make sure this is equal to ilp_obj.model.ObjVal
            logging.info(f'New modularity of graph after {i + 1}th ILP iteration: {new_modularity}')
            delta_Q = new_modularity - curr_modularity
            logging.info(f'Delta Q modularity is: {delta_Q}')
            if delta_Q > 0:
                num_communities_divided_by_ilp += 1
                logging.info(
                    f'Delta Q modularity is ++positive++: {delta_Q}. Adding ILP division to {len(ilp_obj.communities)} communities.')
                curr_communities = ilp_obj.communities  # New division
            else:
                logging.info(f'Delta Q modularity is --Negative-- or Zero: {delta_Q}.Not adding ILP division.')
                curr_communities = [nodes_list]  # Initial division

        except Exception:  # need to make this exception more specific (timeout)
            logging.info(f'passed timeout time, adding community without further division.')
            curr_communities = [nodes_list]  # Don't divide subgraph more

        logging.info(f'Num of curr_communities: {len(curr_communities)}')
        final_communities += curr_communities
    logging.info(
        f"Num of communities skipped by ILP (len(comm))> lp_critical) algo is {num_communities_skipped_by_ilp}/{len(neumann_communities)}")
    logging.info(
        f"Num of communities changed by ILP algo is {num_communities_divided_by_ilp}/{len(neumann_communities)}")
    return final_communities


class NetworkObj:
    def __init__(self, main_dp, network_name):
        self.network_name = network_name
        print("main_dp: ", main_dp)
        print("network_name: ", network_name)
        self.save_directory_path = init_results_folder(main_dp, network_name)
        self.network_dp = os.path.join(PATH2SHANIS_GRAPHS, self.network_name)
        self.real_communities = read_communities_file(os.path.join(self.network_dp, "community.dat"))
        _pickle(os.path.join(self.save_directory_path, "real.communities"), self.real_communities, is_dump=True)
        self.G = create_graph_from_edge_file(os.path.join(self.network_dp, "network.dat"))  # creating graph object
        self.binary_input_fp = create_binary_network_file(self.G, self.save_directory_path, title=self.network_name,
                                                          is_shanis_file=True)  # converting network to binary file


# run on all of shani's networks
def multi_run(lp_criticals):
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)
    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True)[:5]:
        one_run(input_network_folder,path2curr_date_folder,lp_criticals)


def one_run(input_network_folder, path2curr_date_folder, lp_criticals):
    ########### define logger output ##############
    setup_logger(os.path.join(path2curr_date_folder, input_network_folder))

    logging.info(f'Starting to run algos on input_network_folder= {input_network_folder}')
    eval_results_per_network = []  # Save all final results in this list (for creating df later)
    network_obj = NetworkObj(path2curr_date_folder, input_network_folder)

    logging.info(f'===================== Running: Neumann C =======================')
    start = timer()
    neumann_communities = get_neumann_communities(network_obj.save_directory_path, network_obj.network_name,
                                                  network_obj.binary_input_fp)
    end = timer()
    save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                  network_obj.real_communities,
                  new_communities=neumann_communities, algo="Neumann", time=end - start)
    logging.info(f'===================== Running: Louvain networkx =======================')
    start = timer()
    louvain_communities = louvain(network_obj.G)
    end = timer()
    save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                  network_obj.real_communities,
                  new_communities=louvain_communities, algo="Louvain", time=end - start)

    logging.info(
        f'===================== Running: Neumann C + ILP (according to timeit) regular =======================')
    for lp_critical in lp_criticals:
        logging.info(f'=================== LP_critical={lp_critical} ===============')
        start = timer()
        neuman_com_partial_run = get_neumann_communities(network_obj.save_directory_path, network_obj.network_name,
                                                         network_obj.binary_input_fp, lp_critical=lp_critical)
        neumann_ilp_com = run_ilp_on_neumann(network_obj.G, neuman_com_partial_run, lp_critical=lp_critical)
        end = timer()
        save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                      network_obj.real_communities,
                      new_communities=neumann_ilp_com, algo=f'Neumann-ILP-{lp_critical}', time=end - start)

        logging.info(f'=================== LP_critical={lp_critical} -IntFeasTol ===============')
        start = timer()
        neuman_com_partial_run = get_neumann_communities(network_obj.save_directory_path, network_obj.network_name,
                                                         network_obj.binary_input_fp, lp_critical=lp_critical)
        neumann_ilp_com = run_ilp_on_neumann(network_obj.G, neuman_com_partial_run, lp_critical=lp_critical,IntFeasTol=float(1e-3))
        end = timer()
        save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                      network_obj.real_communities,
                      new_communities=neumann_ilp_com, algo=f'Neumann-ILP-{lp_critical}-{float(1e-3)}', time=end - start)

        logging.info(f'=================== LP_critical={lp_critical} -Time limit ===============')
        start = timer()
        neuman_com_partial_run = get_neumann_communities(network_obj.save_directory_path, network_obj.network_name,
                                                         network_obj.binary_input_fp, lp_critical=lp_critical)
        neumann_ilp_com = run_ilp_on_neumann(network_obj.G, neuman_com_partial_run, lp_critical=lp_critical,TimeLimit=True)
        end = timer()
        save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                      network_obj.real_communities,
                      new_communities=neumann_ilp_com, algo=f'Neumann-ILP-{lp_critical}-TimeLimit-60', time=end - start)

    # Finished
    logging.info(f'Finished running algos on input_network_folder= {input_network_folder}')
    # Create df per network
    logging.info(f'Creating DF for this network:')
    data_dict = create_data_dict(eval_results_per_network)
    df = pd.DataFrame(data_dict)
    df.to_pickle(os.path.join(network_obj.save_directory_path, "results.df"))
    csv_name = f"results_df-{input_network_folder}.csv"
    df.to_csv(os.path.join(network_obj.save_directory_path, csv_name))
    # prompt_file(os.path.join(network_obj.save_directory_path, csv_name))


if __name__ == '__main__':
    lp_critical_list = [100,150]
    multi_run(lp_critical_list)
    # one_run("1000_0.6_7")
    pass
