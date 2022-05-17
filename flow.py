import os
from timeit import default_timer as timer
import pandas as pd
import logging
from algorithms.algorithms import louvain
from algorithms.modified_louvain import modified_louvain_communities
from binary_files import create_binary_network_file
from consts import PATH2SHANIS_GRAPHS, FOLDER2FLOW_RESULTS
from evaluation import calc_modularity_manual
from input_networks import create_graph_from_edge_file, read_communities_file
from helpers import init_results_folder, _pickle
from logger import setup_logger
from output_generator import generate_outputs_for_community_list, save_and_eval
from algorithms.ilp import ILP, convert_mega_com_to_regular
from algorithms.Neumann import get_neumann_communities
from output_generator import save_and_eval, create_data_dict
from algorithms.ilp import run_ilp_on_neumann, run_ilp_on_louvain

class AlgoRes:
    def __init__(self, communities: list, lp_critical=None, num_coms_divided=None, num_coms_skipped=None):
        self.communities = communities
        self.lp_critical = None
        self.num_coms_divided = None
        self.num_coms_skipped = None
        self.runtime = None

    def set_runtime(self, runtime):
        self.runtime = runtime


def run_ilp_on_neumann(G, neumann_communities: [list], lp_critical: int, IntFeasTol=float(1e-5), withTimeLimit=False, TimeLimit=0):
    final_communities = []
    num_communities_divided_by_ilp = 0
    num_communities_skipped_by_ilp = 0
    num_to_divide = sum([len(x)<=lp_critical for x in neumann_communities])
    logging.info(f'num_to_divide: {num_to_divide}')
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
        logging.info(f'============Trying to run ILP')
        if withTimeLimit:
            ilp_obj = ILP(G, nodes_list, IntFeasTol, TimeLimit=TimeLimit/num_to_divide)
        else:
            ilp_obj = ILP(G, nodes_list, IntFeasTol)
        new_modularity = calc_modularity_manual(G,
                                                ilp_obj.communities)  # TODO: make sure this is equal to ilp_obj.model.ObjVal
        logging.debug("ILP results===================================")
        logging.info(f'New modularity of graph after {i + 1}th ILP iteration: {new_modularity}')
        delta_Q = new_modularity - curr_modularity
        logging.info(f'Delta Q modularity is: {delta_Q}')
        assert delta_Q >= 0, "delta Q should be none-negative (best is trivial division)"
        if delta_Q > 0 and len(ilp_obj.communities) > 1:
            num_communities_divided_by_ilp += 1
            logging.info(
                f'Delta Q modularity is ++positive++: {delta_Q}. Adding ILP division to {len(ilp_obj.communities)} communities.')
            curr_communities = ilp_obj.communities  # New division
        else:
            logging.info(f'Delta Q modularity is Zero: {delta_Q}. Not adding ILP division.')
            curr_communities = [nodes_list]  # Initial division

        logging.info(f'Num of curr_communities: {len(curr_communities)}')
        final_communities += curr_communities
    logging.info(
        f"Num of communities skipped by ILP (len(comm))> lp_critical) algo is {num_communities_skipped_by_ilp}/{len(neumann_communities)}")
    logging.info(
        f"Num of communities changed by ILP algo is {num_communities_divided_by_ilp}/{len(neumann_communities)}")

    ilp_results_obj = AlgoRes(communities=final_communities)
    ilp_results_obj.lp_critical = lp_critical
    ilp_results_obj.num_coms_divided = num_communities_divided_by_ilp
    ilp_results_obj.num_coms_skipped = num_communities_skipped_by_ilp

    return ilp_results_obj
from algorithms.ilp import run_ilp_on_neumann, run_ilp_on_louvain
from algorithms.Neumann import get_neumann_communities


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
def multi_run(lp_critical_values):
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)
    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True):
        # one_run(input_network_folder, path2curr_date_folder, lp_critical_values)
        for critical in lp_critical_values:
            run_one_louvain(input_network_folder, path2curr_date_folder, critical)


def run_one_louvain(input_network_folder, path2curr_date_folder, louvain_critical):
    # define logger output ##############
    setup_logger(os.path.join(path2curr_date_folder, input_network_folder))
    eval_results_per_network = []  # Save all final results in this list (for creating df later)
    logging.info(f'Starting to run algos on input_network_folder= {input_network_folder}')
    network_obj = NetworkObj(path2curr_date_folder, input_network_folder)

    logging.info(f'===================== Running: Louvain networkx =======================')
    start = timer()
    louvain_communities = louvain(network_obj.G)
    end = timer()
    save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                  network_obj.real_communities,
                  new_communities=louvain_communities, algo="Louvain", time=end - start)


    logging.info(f'===================== Running: Louvain Changed networkx =======================')
    start = timer()
    mega_graph = modified_louvain_communities(network_obj.G, num_com_bound=louvain_critical)
    logging.warning(f"Number nodes mega_graph: \n{mega_graph.number_of_nodes()}")
    mega_communities_partition = run_ilp_on_louvain(mega_graph)
    curr_communities = convert_mega_com_to_regular(mega_graph, mega_communities_partition)
    end = timer()
    print(f"num of final communities: \n{len(curr_communities)}")
    save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                  network_obj.real_communities,
                  new_communities=curr_communities, algo=f'louvain-ILP-num_com_bound {louvain_critical}', time=end - start)
    create_outputs(input_network_folder, eval_results_per_network, network_obj)


def one_run(input_network_folder, path2curr_date_folder, lp_criticals):
    # define logger output ##############
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
        neumann_ilp_com = run_ilp_on_neumann(network_obj.G, neuman_com_partial_run, lp_critical=lp_critical,
                                             IntFeasTol=float(1e-3))
        end = timer()
        save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                      network_obj.real_communities,
                      new_communities=neumann_ilp_com, algo=f'Neumann-ILP-{lp_critical}-{float(1e-3)}',
                      time=end - start)

        logging.info(f'=================== LP_critical={lp_critical} -Time limit ===============')
        start = timer()
        neuman_com_partial_run = get_neumann_communities(network_obj.save_directory_path, network_obj.network_name,
                                                         network_obj.binary_input_fp, lp_critical=lp_critical)
        TimeLimit = 5 * 60  # in seconds
        neumann_ilp_com = run_ilp_on_neumann(network_obj.G, neuman_com_partial_run, lp_critical=lp_critical,
                                             withTimeLimit=True, TimeLimit=TimeLimit)
        end = timer()
        save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                      network_obj.real_communities,
                      new_communities=neumann_ilp_com, algo=f'Neumann-ILP-{lp_critical}-TimeLimit-{TimeLimit}',
                      time=end - start)

    # Finished
    create_outputs(input_network_folder, eval_results_per_network, network_obj)


def create_outputs(input_network_folder, eval_results_per_network, network_obj):
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
    lp_critical_list = [100, 150, 200]
    # multi_run(lp_critical_list)
    # one_run("1000_0.6_7")
    # run_one_louvain("1000_0.6_7", init_results_folder(FOLDER2FLOW_RESULTS), 200)
    multi_run(lp_critical_list)
    pass
