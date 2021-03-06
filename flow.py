import os
from timeit import default_timer as timer
import pandas as pd
import logging
from algorithms.algorithms import louvain
from algorithms.modified_louvain import modified_louvain_communities
from algorithms.mega_nodes_utils import unite_mega_nodes_and_convert2communities, split_mega_nodes, \
    modularity_split_mega_node, \
    min_cut_split_mega_node, random_split_mega_node, ilp_split_mega_node, ilp_split_mega_node_whole_graph, \
    newman_split_mega_nodes_whole_graph, newman_split_mega_nodes_sub_graph
from utils.binary_files import create_binary_network_file
from consts import FOLDER2FLOW_RESULTS, default_lp_list
from utils.evaluation import calc_modularity_manual, calc_modularity_nx
from utils.helpers import init_results_folder, read_graph_files, current_time
from algorithms.ilp.ilp_max_mod_union import ILP
from utils.output_generator import save_and_eval, create_data_dict
from algorithms.neumann_utils import get_neumann_communities


def run(run_obj, network_obj):
    if run_obj.algorithm == "louvain":
        return run_with_comparison_louvain(network_obj, run_obj)
    else:  # run_obj.algorithm == "newman":
        return run_with_comparison_newman(network_obj, run_obj)


# ------------------------------- Louvain -------------------------------

# add try catch to run ilp .. bc of out of memory
def run_with_comparison_louvain(network_obj, run_obj):
    eval_results_per_network = []
    if run_obj.with_comparison:
        logging.debug(f'===================== Running: Louvain networkx =======================')
        logging.info(f"Running original Louvain for comparison")
        for i in range(run_obj.number_runs_original_louvain):
            run_louvain(eval_results_per_network, network_obj, run_obj)
    logging.debug(f'===================== Running: Louvain Changed networkx =======================')
    logging.info(f"Running changed Louvain")
    louvain_change_communities = run_louvain_with_change(eval_results_per_network,
                                                         network_obj,
                                                         run_obj
                                                         )
    create_outputs(network_obj.network_name, eval_results_per_network, network_obj.save_directory_path)
    logging.debug(f'eval_results_per_network={eval_results_per_network}')
    delete_in_run_files(network_obj.save_directory_path)
    return louvain_change_communities


def run_ilp_on_louvain(G, TimeLimit):
    '''
    :param TimeLimit:
    :param G: graph with MEGA nodes
    :return: communities
    '''
    nodes_list = list(G.nodes)
    mod_mega_graph_divided = calc_modularity_nx(G, [[n] for n in nodes_list], weight="weight")
    mod_mega_graph_full = calc_modularity_nx(G, [nodes_list], weight="weight")
    logging.debug(f'============Trying to run ILP============')
    if TimeLimit is not None:
        ilp_obj = ILP(G, nodes_list, TimeLimit=TimeLimit, weight="weight")
    else:
        ilp_obj = ILP(G, nodes_list, weight="weight")
    logging.debug("============ILP results============")
    mod_new = calc_modularity_nx(G, ilp_obj.communities, weight="weight")

    logging.debug(
        f'Extra: Modularity of graph before ILP iteration - nx calculation full graph: {mod_mega_graph_full}\n')  # for debugging - delete soon
    logging.debug(
        f'Modularity of graph before ILP iteration - nx calculation divided graph (used for delta): {mod_mega_graph_divided}')
    logging.debug(f'New modularity of graph after ILP iteration: {mod_new}\n')

    delta_Q = mod_new - mod_mega_graph_divided
    logging.debug(f'Delta Q modularity is: {delta_Q}')

    if delta_Q > 0 and len(ilp_obj.communities) > 1:
        logging.debug(
            f'Delta Q modularity is ++positive++: {delta_Q}. Adding ILP division to {len(ilp_obj.communities)} communities.')
        curr_mega_communities = ilp_obj.communities  # New division
    else:
        logging.debug(f'Delta Q modularity is --Negative-- or Zero: {delta_Q}.Not adding ILP division.')
        curr_mega_communities = [nodes_list]  # Initial division
    logging.debug(f'Num of curr_mega_communities: {len(curr_mega_communities)}')
    return curr_mega_communities


def run_louvain(eval_results_per_network, network_obj, run_obj):
    start = timer()
    louvain_communities = louvain(network_obj.G)
    end = timer()
    logging.debug(f'Finished runnning regular Louvain: num communties = {len(louvain_communities)}')

    save_and_eval(
        network_obj.save_directory_path,
        eval_results_per_network,
        "Louvain",
        network_obj,
        run_obj,
        louvain_communities,
        time=end - start,
    )


def run_louvain_with_change(
        eval_results_per_network,
        network_obj,
        run_obj,
):
    for critical in run_obj.lp_list:
        logging.debug(f'lp_critical={critical}, timelimit={run_obj.TimeLimit}')
        start = timer()
        iterations_number, mega_graph = modified_louvain_communities(network_obj.G, num_com_bound=critical)
        run_obj.critical = critical
        logging.info(
            f'Finished runnning partially regular Louvain: num nodes mega graph = {mega_graph.number_of_nodes()}')
        try:
            network_obj.number_of_mega_nodes_before_split = mega_graph.number_of_nodes()
            # split mega graph
            if run_obj.split_method is not None:

                if run_obj.split_method == "newman_whole_graph":
                    mega_graph = newman_split_mega_nodes_whole_graph(network_obj, mega_graph)
                elif run_obj.split_method == "newman_sub_graph":
                    mega_graph = newman_split_mega_nodes_sub_graph(network_obj, mega_graph)
                else:
                    mega_graph = split_mega_nodes(network_obj.G, mega_graph, critical, run_obj)
                logging.info(f'Tried splitting nodes. num of nodes in mega is {mega_graph.number_of_nodes()}')

            # regular run
            number_of_mega_nodes = mega_graph.number_of_nodes()
            network_obj.number_of_mega_nodes = number_of_mega_nodes
            if network_obj.number_of_mega_nodes_before_split <= critical:
                logging.info(f"Running ilp on louvain")
                mega_communities_partition = run_ilp_on_louvain(mega_graph, run_obj.TimeLimit)
            else:
                logging.info(
                    f"Not running run_ilp_on_louvain because num of mega nodes- {network_obj.number_of_mega_nodes_before_split} > lp_critical - {critical}")
                mega_communities_partition = [mega_graph.nodes]
            curr_communities = unite_mega_nodes_and_convert2communities(mega_graph, mega_communities_partition)
            end = timer()
            # run_obj.communities = curr_communities
            network_obj.iterations_number = iterations_number
            logging.info(f"Finished running ILP Louvain: num of final communities: {len(curr_communities)}")
            save_and_eval(
                network_obj.save_directory_path,
                eval_results_per_network,
                f'LLP-{critical}',
                network_obj,
                run_obj,
                curr_communities,
                end - start)
            logging.debug(f'------ success running ilp on louvain, lp_critical={critical}')
            return curr_communities
        except Exception as e:
            logging.debug(
                f'run_one_louvain didnt work on {network_obj.network_name}, lp_critical={critical}')
            logging.error(e)
            raise e
    create_outputs(network_obj.network_name, eval_results_per_network, network_obj.save_directory_path)
    delete_in_run_files(network_obj.save_directory_path)
    logging.debug(f'eval_results_per_network={eval_results_per_network}')


# ------------------------------- Newman -------------------------------
def run_with_comparison_newman(network_obj, run_obj):
    eval_results_per_network = []
    if run_obj.with_comparison:
        logging.info(f"Running original Louvain for comparison")
        logging.debug(f'===================== Running: Louvain networkx =======================')
        run_louvain(eval_results_per_network, network_obj, run_obj)
        logging.info(f"Running original Neumann for comparison")
        logging.debug(f'===================== Running: Neumann C =======================')
        run_newman(
            eval_results_per_network,
            run_obj,
            network_obj)
    logging.info(f"Running changed Neumann for comparison")
    logging.debug(f'===================== Running: Neumann C changed=======================')
    communities = run_newman_with_change(
        eval_results_per_network,
        run_obj,
        network_obj,
    )
    # Finished

    create_outputs(network_obj.network_name, eval_results_per_network, network_obj.save_directory_path)
    delete_in_run_files(network_obj.save_directory_path)
    logging.debug(f'eval_results_per_network={eval_results_per_network}')
    return communities


def run_ilp_on_neumann(network_obj,
                       run_obj,
                       neumann_communities: [list],
                       lp_critical: int,
                       ):
    final_communities = []
    num_communities_divided_by_ilp = 0
    num_communities_skipped_by_ilp = 0
    num_to_divide = sum([len(x) <= lp_critical for x in neumann_communities])
    logging.debug(f'num_to_divide: {num_to_divide} groups')
    for i in range(len(neumann_communities)):
        nodes_list = neumann_communities[i]
        num_nodes = len(nodes_list)
        logging.debug(
            f'============== Iteration {i + 1}/{len(neumann_communities)}, subgraph size = {num_nodes} ================')
        if num_nodes > lp_critical:  # This community already reached maximal modularity - no need to divide more
            logging.debug(f'num nodes {num_nodes} > lp_critical {lp_critical}, skipping.')
            num_communities_skipped_by_ilp += 1
            curr_communities = [nodes_list]
            final_communities += curr_communities
            continue

        curr_modularity = calc_modularity_manual(network_obj.G,
                                                 [nodes_list])  # Modularity before dividing more with ILP
        logging.debug(f'Modularity of graph before {i + 1}th ILP iteration: {curr_modularity}')
        logging.debug(f'============Trying to run ILP')
        if run_obj.TimeLimit is not None:
            time_per_run = run_obj.TimeLimit / num_to_divide
            logging.debug(f'time_per_run: {time_per_run} seconds')
            ilp_obj = ILP(network_obj.G, nodes_list, TimeLimit=time_per_run)
        else:
            ilp_obj = ILP(network_obj.G, nodes_list)
        new_modularity = calc_modularity_manual(network_obj.G,
                                                ilp_obj.communities)  # TODO: make sure this is equal to ilp_obj.model.ObjVal
        logging.debug("ILP results===================================")
        logging.debug(f'New modularity of graph after {i + 1}th ILP iteration: {new_modularity}')
        delta_Q = new_modularity - curr_modularity
        logging.debug(f'Delta Q modularity is: {delta_Q}')
        assert delta_Q >= 0, "delta Q should be none-negative (best is trivial division)"
        if delta_Q > 0 and len(ilp_obj.communities) > 1:
            num_communities_divided_by_ilp += 1
            logging.debug(
                f'Delta Q modularity is ++positive++: {delta_Q}. Adding ILP division to {len(ilp_obj.communities)} communities.')
            curr_communities = ilp_obj.communities  # New division
        else:
            assert (delta_Q == 0)
            logging.debug(f'Delta Q modularity is Zero: {delta_Q}. Not adding ILP division.')
            curr_communities = [nodes_list]  # Initial division

        logging.debug(f'Num of curr_communities: {len(curr_communities)}')
        final_communities += curr_communities
    logging.debug(
        f"Num of communities skipped by ILP (len(comm))> lp_critical) algo is {num_communities_skipped_by_ilp}/{len(neumann_communities)}"
    )
    logging.debug(
        f"Num of communities changed by ILP algo is {num_communities_divided_by_ilp}/{len(neumann_communities)}"
    )
    num_coms_divided = num_communities_divided_by_ilp
    num_coms_skipped = num_communities_skipped_by_ilp
    return final_communities, num_coms_divided, num_coms_skipped


def run_newman(eval_results_per_network, run_obj, network_obj):
    start = timer()
    neumann_communities = get_neumann_communities(network_obj.save_directory_path,
                                                  network_obj.network_name,
                                                  network_obj.graph_binary_input_fp
                                                  )
    end = timer()
    save_and_eval(network_obj.save_directory_path,
                  eval_results_per_network,
                  "Newman",
                  network_obj,
                  run_obj,
                  neumann_communities,
                  end - start)


def run_newman_with_change(eval_results_per_network, run_obj, network_obj):
    for lp_critical in run_obj.lp_list:
        logging.debug(f'=================== LP_critical={lp_critical} -Time limit ===============')
        start = timer()
        neuman_com_partial_run = get_neumann_communities(network_obj.save_directory_path,
                                                         network_obj.network_name,
                                                         network_obj.graph_binary_input_fp,
                                                         lp_critical=lp_critical,
                                                         )
        TimeLimit = run_obj.TimeLimit  # in seconds
        logging.info(f"Running ILP-partition on newman")
        final_communities, network_obj.num_coms_divided, network_obj.num_coms_skipped = run_ilp_on_neumann(
            network_obj,
            run_obj,
            neuman_com_partial_run,
            lp_critical=lp_critical,
        )

        end = timer()
        save_and_eval(
            network_obj.save_directory_path,
            eval_results_per_network,
            f'NLP-{lp_critical}-TL-{TimeLimit}',
            network_obj,
            run_obj,
            final_communities,
            end - start,
        )
        return final_communities


# ------------------------------- Helper classes -------------------------------
class NetworkObj:
    def __init__(self,
                 network_path,
                 run_obj
                 ):
        self.network_name = os.path.basename(os.path.normpath(network_path))
        self.save_directory_path = init_results_folder(run_obj.path2curr_date_folder, self.network_name)
        self.network_dp = network_path
        self.G, self.real_communities, self.network_dictionary = read_graph_files(self.network_dp, run_obj)
        # _pickle(os.path.join(self.save_directory_path, "real.communities"), self.real_communities, is_dump=True)
        self.graph_binary_input_fp = create_binary_network_file(self.G, self.save_directory_path,
                                                                title=self.network_name)  # converting network to binary file
        self.communities_binary_input_fp = None

        # moved
        self.mega_communities = None
        self.number_of_mega_nodes = None
        self.num_coms_divided = None
        self.num_coms_skipped = None
        self.iterations_number = None
        self.number_of_mega_nodes_before_split = None


class RunParamInfo:
    def __init__(self,
                 algorithm="louvain",
                 split_method="newman_whole_graph",
                 lp_list=default_lp_list,
                 TimeLimit=60 * 10,
                 folder_name="",
                 max_mega_node_split_size=float("inf"),
                 number_runs_original_louvain=1,
                 community_file_name="community.dat",
                 network_file_name="network.dat",
                 with_comparison_to_newman_louvain=True,
                 log_to_file=True,
                 console_log_level="info"

                 ):
        self.folder_name = f"{current_time()}-{folder_name}"
        self.algorithm = algorithm
        self.path2curr_date_folder = None
        self.lp_list = lp_list
        self.split_method = split_method
        self.split_methods = {
            "mod_greedy": modularity_split_mega_node,
            "min_cut": min_cut_split_mega_node,
            "random": random_split_mega_node,
            "ilp_sub_graph": ilp_split_mega_node,
            "ilp_whole_graph": ilp_split_mega_node_whole_graph,
            "newman_whole_graph": newman_split_mega_nodes_whole_graph,
            "newman_sub_graph": newman_split_mega_nodes_sub_graph,
        }
        self.critical = None
        self.TimeLimit = TimeLimit
        self.max_mega_node_split_size = max_mega_node_split_size
        self.number_runs_original_louvain = number_runs_original_louvain
        self.community_file_name = community_file_name
        self.network_file_name = network_file_name
        self.with_comparison = with_comparison_to_newman_louvain
        self.log_to_file = log_to_file
        self.console_log_level = console_log_level

    def init_results_folder(self):
        self.path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS,
                                                         folder_name=self.folder_name)


# ------------------------------- Helper functions -------------------------------

def create_outputs(input_network_folder, eval_results_per_network, save_directory_path):
    # Finished
    logging.info(
        f'Finished running algo. your output is here:\n {save_directory_path}')
    # Create df per network
    logging.debug(f'Creating DF for this network')
    data_dict = create_data_dict(eval_results_per_network)
    df = pd.DataFrame(data_dict)
    df.to_pickle(os.path.join(save_directory_path, "results.df"))
    csv_name = f"results_df-{input_network_folder}.csv"
    df.to_csv(os.path.join(save_directory_path, csv_name))


def delete_in_run_files(path):
    files = os.listdir(path)
    for item in files:
        if item.endswith(".in") or item.endswith(".out"):
            os.remove(os.path.join(path, item))

