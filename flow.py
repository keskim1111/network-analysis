import os
from timeit import default_timer as timer
import pandas as pd
import logging
from algorithms.algorithms import louvain
from algorithms.modified_louvain import modified_louvain_communities
from binary_files import create_binary_network_file
from consts import PATH2SHANIS_GRAPHS, FOLDER2FLOW_RESULTS
from evaluation import calc_modularity_manual, calc_modularity_nx
from input_networks import create_graph_from_edge_file, read_communities_file
from helpers import init_results_folder, _pickle, prompt_file
from logger import setup_logger
from algorithms.ilp import ILP, convert_mega_com_to_regular
from output_generator import save_and_eval, create_data_dict
from algorithms.Neumann import get_neumann_communities
from networkx.algorithms.community import modularity


class AlgoRes:
    def __init__(self, communities=None,mega_communities=None):
        self.communities = communities
        self.mega_communities = mega_communities
        self.number_of_mega_nodes = None
        self.critical = None
        self.num_coms_divided = None
        self.num_coms_skipped = None
        self.runtime = None
        self.iterations_number = None

    def set_runtime(self, runtime):
        self.runtime = runtime


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


# ======================================== Louvain ======================================================
def multi_run_louvain(timelimit):
    lp_critical_for_1000 = [100]*10
    lp_critical_for_10000 = [70, 150]
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)
    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True):
        if "10000" in input_network_folder:
            # run_one_louvain(input_network_folder, path2curr_date_folder, lp_critical_for_10000, withTimeLimit=True, TimeLimit=timelimit)
            continue
        else: # TODO: add running of 10 times per network - and put results in the same df
            # continue
            run_one_louvain(input_network_folder, path2curr_date_folder, lp_critical_for_1000)


# add try catch to run ilp .. bc of out of memory
def run_one_louvain(input_network_folder, path2curr_date_folder, lp_critical_values,  withTimeLimit=False, TimeLimit=0):
    # define logger output ##############
    setup_logger(os.path.join(path2curr_date_folder, input_network_folder), log_to_file=True)
    eval_results_per_network = []  # Save all final results in this list (for creating df later)
    logging.info(f'Starting to run algos on input_network_folder= {input_network_folder}')
    network_obj = NetworkObj(path2curr_date_folder, input_network_folder)

    logging.info(f'===================== Running: Louvain networkx =======================')
    start = timer()
    louvain_communities = louvain(network_obj.G)
    end = timer()
    logging.warning(f'Finished runnning regular Louvain: num communties = {len(louvain_communities)}')
    save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                  network_obj.real_communities,
                  new_communities=louvain_communities, algo="Louvain", time=end - start)

    logging.info(f'===================== Running: Louvain Changed networkx =======================')
    for critical in lp_critical_values:
        logging.warning(f'lp_critical={critical}, withTimeLimit={withTimeLimit}, timelimit={TimeLimit}')
        start = timer()
        iterations_number, mega_graph = modified_louvain_communities(network_obj.G, num_com_bound=critical)

        ilp_results_obj = AlgoRes()
        number_of_mega_nodes = mega_graph.number_of_nodes()
        ilp_results_obj.number_of_mega_nodes = number_of_mega_nodes
        ilp_results_obj.critical = critical
        logging.warning(f'Finished runnning regular Louvain: num nodes mega graph = {mega_graph.number_of_nodes()}')
        try:
            logging.info(f'about to run_ilp_on_louvain')
            mega_communities_partition = run_ilp_on_louvain(mega_graph,  withTimeLimit=withTimeLimit, TimeLimit=TimeLimit)
            curr_communities = convert_mega_com_to_regular(mega_graph, mega_communities_partition)
            end = timer()
            ilp_results_obj.communities = curr_communities
            ilp_results_obj.iterations_number = iterations_number
            ilp_results_obj.runtime = end - start
            logging.warning(f"Finished running ILP Louvain: num of final communities: {len(curr_communities)}")
            save_and_eval(
                          network_obj.save_directory_path,
                          eval_results_per_network,
                          network_obj.G,
                          network_obj.real_communities,
                          new_communities=curr_communities,
                          algo=f'LLP-{critical}',
                          time=end - start,
                          extra_evals=ilp_results_obj)
            logging.info(f'------ success running ilp on louvain, lp_critical={critical}')
        except Exception as e:
            logging.info(f'run_one_louvain didnt work on {input_network_folder}, lp_critical={critical}, number_of_mega_nodes={number_of_mega_nodes}')
            logging.debug(e)
    create_outputs(input_network_folder, eval_results_per_network, network_obj)
    logging.info(f'eval_results_per_network={eval_results_per_network}')


def run_ilp_on_louvain(G, withTimeLimit=False, TimeLimit=0):
    '''
    :param G: graph with MEGA nodes
    :return: communites
    '''
    nodes_list = list(G.nodes)
    # curr_modularity = calc_modularity_manual(G, [nodes_list],weight="weight")  # Modularity before dividing more with ILP
    mod_mega_graph_divided = calc_modularity_nx(G, [[n] for n in nodes_list], weight="weight")
    mod_mega_graph_full = calc_modularity_nx(G, [nodes_list], weight="weight")

    logging.info(f'============Trying to run ILP')
    if withTimeLimit:
        ilp_obj = ILP(G, nodes_list, TimeLimit=TimeLimit, weight="weight")
    else:
        ilp_obj = ILP(G, nodes_list, weight="weight")
    # new_modularity = calc_modularity_manual(G,
    #                                         ilp_obj.communities,weight="weight")  # TODO: make sure this is equal to ilp_obj.model.ObjVal
    logging.debug("ILP results===================================")
    mod_new = calc_modularity_nx(G, ilp_obj.communities, weight="weight")

    logging.warning(f'Extra: Modularity of graph before ILP iteration - nx calculation full graph: {mod_mega_graph_full}\n') # for debugging - delete soon

    logging.warning(f'Modularity of graph before ILP iteration - nx calculation divided graph (used for delta): {mod_mega_graph_divided}')
    logging.warning(f'New modularity of graph after ILP iteration: {mod_new}\n')

    delta_Q = mod_new - mod_mega_graph_divided
    logging.info(f'Delta Q modularity is: {delta_Q}')

    if delta_Q > 0 and len(ilp_obj.communities) > 1:
        logging.warning(
            f'Delta Q modularity is ++positive++: {delta_Q}. Adding ILP division to {len(ilp_obj.communities)} communities.')
        curr_mega_communities = ilp_obj.communities  # New division
    else:
        logging.warning(f'Delta Q modularity is --Negative-- or Zero: {delta_Q}.Not adding ILP division.')
        curr_mega_communities = [nodes_list]  # Initial division
    logging.warning(f'Num of curr_mega_communities: {len(curr_mega_communities)}')
    return curr_mega_communities


# ======================================== Newman ======================================================
# TODO: add column of average subgraph size (that was run by ILP).
def multi_run_newman(lp_criticals, lp_timelimit):
    done_dict = {0.4:0, 0.5:0, 0.6:0}
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)
    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True):
        if "10000" in input_network_folder:
            for mu in done_dict.keys():
                if str(mu) in input_network_folder and done_dict[mu] <= 3: # run up to 3 runs per mu
                    done_dict[mu] += 1
                    print(done_dict)
                    print(input_network_folder)
                    run_one_newman(input_network_folder, path2curr_date_folder, lp_criticals, lp_timelimit)


def run_one_newman(input_network_folder, path2curr_date_folder, lp_criticals, lp_timelimit):
    # define logger output ##############
    setup_logger(os.path.join(path2curr_date_folder, input_network_folder))

    logging.info(f'Starting to run algos on input_network_folder= {input_network_folder}')
    eval_results_per_network = []  # Save all final results in this list (for creating df later)
    network_obj = NetworkObj(path2curr_date_folder, input_network_folder)

    logging.info(f'===================== Running: Louvain networkx =======================')
    start = timer()
    louvain_communities = louvain(network_obj.G)
    end = timer()
    save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                  network_obj.real_communities,
                  new_communities=louvain_communities, algo="Louvain", time=end - start)

    logging.info(f'===================== Running: Neumann C =======================')
    start = timer()
    neumann_communities = get_neumann_communities(network_obj.save_directory_path, network_obj.network_name,
                                                  network_obj.binary_input_fp)
    end = timer()
    save_and_eval(network_obj.save_directory_path, eval_results_per_network, network_obj.G,
                  network_obj.real_communities,
                  new_communities=neumann_communities, algo="Newman", time=end - start)

    for lp_critical in lp_criticals:
        logging.info(f'=================== LP_critical={lp_critical} -Time limit ===============')
        start = timer()
        neuman_com_partial_run = get_neumann_communities(network_obj.save_directory_path, network_obj.network_name,
                                                         network_obj.binary_input_fp, lp_critical=lp_critical)
        TimeLimit = lp_timelimit  # in seconds
        newman_ilp_results_obj = run_ilp_on_neumann(network_obj.G, neuman_com_partial_run, lp_critical=lp_critical,
                                                    withTimeLimit=True, TimeLimit=TimeLimit)
        end = timer()
        newman_ilp_results_obj.runtime = end - start
        save_and_eval(
                      network_obj.save_directory_path,
                      eval_results_per_network, network_obj.G,
                      network_obj.real_communities,
                      new_communities=newman_ilp_results_obj.communities,
                      algo=f'NLP-{lp_critical}-TL-{TimeLimit}',
                      time=newman_ilp_results_obj.runtime,
                      extra_evals=newman_ilp_results_obj
                      )

    # Finished
    logging.info(f'Finished running algos on input_network_folder= {input_network_folder}')
    # Create df per network
    logging.info(f'Creating DF for this network')
    data_dict = create_data_dict(eval_results_per_network)
    df = pd.DataFrame(data_dict)
    df.to_pickle(os.path.join(network_obj.save_directory_path, "results.df"))
    csv_name = f"results_df-{input_network_folder}.csv"
    df.to_csv(os.path.join(network_obj.save_directory_path, csv_name))
    # prompt_file(os.path.join(network_obj.save_directory_path, csv_name))


def run_ilp_on_neumann(G, neumann_communities: [list], lp_critical: int, withTimeLimit=False,
                       TimeLimit=0):
    final_communities = []
    num_communities_divided_by_ilp = 0
    num_communities_skipped_by_ilp = 0
    num_to_divide = sum([len(x) <= lp_critical for x in neumann_communities])
    logging.warning(f'num_to_divide: {num_to_divide} groups')
    for i in range(len(neumann_communities)):
        nodes_list = neumann_communities[i]
        num_nodes = len(nodes_list)
        logging.warning(
            f'============== Iteration {i + 1}/{len(neumann_communities)}, subgraph size = {num_nodes} ================')
        if num_nodes > lp_critical:  # This community already reached maximal modularity - no need to divide more
            logging.warning(f'num nodes {num_nodes} > lp_critical {lp_critical}, skipping.')
            num_communities_skipped_by_ilp += 1
            curr_communities = [nodes_list]
            final_communities += curr_communities
            continue

        curr_modularity = calc_modularity_manual(G, [nodes_list])  # Modularity before dividing more with ILP
        logging.info(f'Modularity of graph before {i + 1}th ILP iteration: {curr_modularity}')
        logging.warning(f'============Trying to run ILP')
        if withTimeLimit:
            time_per_run = TimeLimit / num_to_divide
            logging.warning(f'time_per_run: {time_per_run} seconds')
            ilp_obj = ILP(G, nodes_list, TimeLimit=time_per_run)
        else:
            ilp_obj = ILP(G, nodes_list)
        new_modularity = calc_modularity_manual(G,
                                                ilp_obj.communities)  # TODO: make sure this is equal to ilp_obj.model.ObjVal
        logging.warning("ILP results===================================")
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
            assert(delta_Q==0)
            logging.info(f'Delta Q modularity is Zero: {delta_Q}. Not adding ILP division.')
            curr_communities = [nodes_list]  # Initial division

        logging.info(f'Num of curr_communities: {len(curr_communities)}')
        final_communities += curr_communities
    logging.info(
        f"Num of communities skipped by ILP (len(comm))> lp_critical) algo is {num_communities_skipped_by_ilp}/{len(neumann_communities)}")
    logging.info(
        f"Num of communities changed by ILP algo is {num_communities_divided_by_ilp}/{len(neumann_communities)}")

    ilp_results_obj = AlgoRes(communities=final_communities)
    ilp_results_obj.critical = lp_critical
    ilp_results_obj.num_coms_divided = num_communities_divided_by_ilp
    ilp_results_obj.num_coms_skipped = num_communities_skipped_by_ilp

    return ilp_results_obj


def create_outputs(input_network_folder, eval_results_per_network, network_obj):
    # Finished
    logging.info(f'Finished running algos on input_network_folder= {input_network_folder}')
    # Create df per network
    logging.info(f'Creating DF for this network')
    data_dict = create_data_dict(eval_results_per_network)
    df = pd.DataFrame(data_dict)
    df.to_pickle(os.path.join(network_obj.save_directory_path, "results.df"))
    csv_name = f"results_df-{input_network_folder}.csv"
    df.to_csv(os.path.join(network_obj.save_directory_path, csv_name))
    # prompt_file(os.path.join(network_obj.save_directory_path, csv_name))


if __name__ == '__main__':
    # lp_critical_list = [100, 500]
    time = 5*60
    # multi_run_newman(lp_critical_list, time)
    # run_one_newman("1000_0.6_7")
    # run_one_louvain("1000_0.6_7", init_results_folder(FOLDER2FLOW_RESULTS), 200)
    multi_run_louvain(time)
    pass
