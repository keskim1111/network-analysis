import os
from timeit import default_timer as timer
import pandas as pd
import logging
from algorithms.algorithms import louvain
from algorithms.modified_louvain import modified_louvain_communities
from algorithms.mega_nodes_utils import unite_mega_nodes_and_convert2communities, split_mega_nodes, \
    modularity_split_mega_node, \
    min_cut_split_mega_node, random_split_mega_node, ilp_split_mega_node, ilp_split_mega_node_whole_graph, \
    newman_split_mega_nodes_whole_graph
from utils.binary_files import create_binary_network_file
from consts import PATH2SHANIS_GRAPHS, FOLDER2FLOW_RESULTS, PATH2BENCHMARKS_GRAPHS
from utils.evaluation import calc_modularity_manual, calc_modularity_nx
from input_networks import create_graph_from_edge_file, read_communities_file
from helpers import init_results_folder, _pickle, read_graph_files, current_time
from utils.logger import setup_logger
from algorithms.ilp_max_mod_union import ILP
from output_generator import save_and_eval, create_data_dict
from algorithms.neumann_utils import get_neumann_communities


# TODO remove
def multi_shani_run(run_obj):
    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True):
        if run_obj.run_on_10000 and "10000" in input_network_folder:
            if run_obj.algorithm == "louvain":
                run_with_comparison_louvain(input_network_folder, run_obj)
            elif run_obj.algorithm == "newman":
                run_with_comparison_newman(input_network_folder, run_obj)
        if run_obj.run_on_1000 and "1000_" in input_network_folder:
            if run_obj.algorithm == "louvain":
                run_with_comparison_louvain(input_network_folder, run_obj)
            elif run_obj.algorithm == "newman":
                run_with_comparison_newman(input_network_folder, run_obj)



def run(run_obj, network_obj):
    if run_obj.algorithm == "louvain":
        run_with_comparison_louvain(network_obj, run_obj)
    else:  # run_obj.algorithm == "newman":
        run_with_comparison_newman(network_obj, run_obj)


# ------------------------------- Louvain -------------------------------

# add try catch to run ilp .. bc of out of memory
def run_with_comparison_louvain(network_obj, run_obj):
    eval_results_per_network = []
    setup_logger(network_obj.save_directory_path, log_to_file=run_obj.log_to_file)
    if run_obj.with_comparison:
        logging.info(f'===================== Running: Louvain networkx =======================')
        for i in range(run_obj.number_runs_original_louvain):
            run_louvain(eval_results_per_network, network_obj, run_obj)
    logging.info(f'===================== Running: Louvain Changed networkx =======================')
    louvain_change_communities = run_louvain_with_change(eval_results_per_network,
                                                         network_obj,
                                                         run_obj
                                                         )
    create_outputs(network_obj.network_name, eval_results_per_network, network_obj.save_directory_path)
    logging.info(f'eval_results_per_network={eval_results_per_network}')
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
    logging.info(f'============Trying to run ILP============')
    if TimeLimit is not None:
        ilp_obj = ILP(G, nodes_list, TimeLimit=TimeLimit, weight="weight")
    else:
        ilp_obj = ILP(G, nodes_list, weight="weight")
    logging.debug("============ILP results============")
    mod_new = calc_modularity_nx(G, ilp_obj.communities, weight="weight")

    logging.warning(
        f'Extra: Modularity of graph before ILP iteration - nx calculation full graph: {mod_mega_graph_full}\n')  # for debugging - delete soon
    logging.warning(
        f'Modularity of graph before ILP iteration - nx calculation divided graph (used for delta): {mod_mega_graph_divided}')
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


def run_louvain(eval_results_per_network, network_obj, run_obj):
    start = timer()
    louvain_communities = louvain(network_obj.G)
    end = timer()
    logging.warning(f'Finished runnning regular Louvain: num communties = {len(louvain_communities)}')

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
        logging.warning(f'lp_critical={critical}, timelimit={run_obj.TimeLimit}')
        start = timer()
        iterations_number, mega_graph = modified_louvain_communities(network_obj.G, num_com_bound=critical)
        run_obj.critical = critical
        logging.warning(f'Finished runnning regular Louvain: num nodes mega graph = {mega_graph.number_of_nodes()}')
        try:
            logging.info(f'about to run_ilp_on_louvain')
            # split mega graph
            if run_obj.split_method is not None:
                network_obj.number_of_mega_nodes_before_split = mega_graph.number_of_nodes()

                if run_obj.split_method == "newman_whole_graph":
                    mega_graph = newman_split_mega_nodes_whole_graph(network_obj, mega_graph, critical, run_obj)
                else:
                    mega_graph = split_mega_nodes(network_obj.G, mega_graph, critical, run_obj)
                logging.warning(f'Splitted nodes. num of nodes in mega is {mega_graph.number_of_nodes()}')

            # regular run
            number_of_mega_nodes = mega_graph.number_of_nodes()
            network_obj.number_of_mega_nodes = number_of_mega_nodes
            mega_communities_partition = run_ilp_on_louvain(mega_graph, run_obj.TimeLimit)
            curr_communities = unite_mega_nodes_and_convert2communities(mega_graph, mega_communities_partition)
            end = timer()
            # run_obj.communities = curr_communities
            network_obj.iterations_number = iterations_number
            logging.warning(f"Finished running ILP Louvain: num of final communities: {len(curr_communities)}")
            save_and_eval(
                network_obj.save_directory_path,
                eval_results_per_network,
                f'LLP-{critical}',
                network_obj,
                run_obj,
                curr_communities,
                end - start)
            logging.info(f'------ success running ilp on louvain, lp_critical={critical}')
            return curr_communities
        except Exception as e:
            logging.info(
                f'run_one_louvain didnt work on {network_obj.network_name}, lp_critical={critical}')
            logging.error(e)
            raise e
    create_outputs(network_obj.network_name, eval_results_per_network, network_obj.save_directory_path)
    logging.info(f'eval_results_per_network={eval_results_per_network}')


# ------------------------------- Newman -------------------------------
def run_with_comparison_newman(network_obj, run_obj):
    eval_results_per_network = []
    setup_logger(network_obj.save_directory_path, log_to_file=run_obj.log_to_file)
    if run_obj.with_comparison:

        logging.info(f'===================== Running: Louvain networkx =======================')
        run_louvain(eval_results_per_network, network_obj, run_obj)

        logging.info(f'===================== Running: Neumann C =======================')
        run_newman(
            eval_results_per_network,
            run_obj,
            network_obj)

    logging.info(f'===================== Running: Neumann C changed=======================')
    run_newman_with_change(
        eval_results_per_network,
        run_obj,
        network_obj,
    )
    # Finished

    create_outputs(network_obj.network_name, eval_results_per_network, network_obj.save_directory_path)
    logging.info(f'eval_results_per_network={eval_results_per_network}')


def run_ilp_on_neumann(network_obj,
                       run_obj,
                       neumann_communities: [list],
                       lp_critical: int,
                       ):
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

        curr_modularity = calc_modularity_manual(network_obj.G,
                                                 [nodes_list])  # Modularity before dividing more with ILP
        logging.info(f'Modularity of graph before {i + 1}th ILP iteration: {curr_modularity}')
        logging.warning(f'============Trying to run ILP')
        if run_obj.TimeLimit is not None:
            time_per_run = run_obj.TimeLimit / num_to_divide
            logging.warning(f'time_per_run: {time_per_run} seconds')
            ilp_obj = ILP(network_obj.G, nodes_list, TimeLimit=time_per_run)
        else:
            ilp_obj = ILP(network_obj.G, nodes_list)
        new_modularity = calc_modularity_manual(network_obj.G,
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
            assert (delta_Q == 0)
            logging.info(f'Delta Q modularity is Zero: {delta_Q}. Not adding ILP division.')
            curr_communities = [nodes_list]  # Initial division

        logging.info(f'Num of curr_communities: {len(curr_communities)}')
        final_communities += curr_communities
    logging.info(
        f"Num of communities skipped by ILP (len(comm))> lp_critical) algo is {num_communities_skipped_by_ilp}/{len(neumann_communities)}"
    )
    logging.info(
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
        logging.info(f'=================== LP_critical={lp_critical} -Time limit ===============')
        start = timer()
        neuman_com_partial_run = get_neumann_communities(network_obj.save_directory_path,
                                                         network_obj.network_name,
                                                         network_obj.graph_binary_input_fp,
                                                         lp_critical=lp_critical,
                                                         )
        TimeLimit = run_obj.TimeLimit  # in seconds
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




# ------------------------------- Helper classes -------------------------------
class NetworkObj:
    def __init__(self,
                 network_path,
                 run_obj
                 ):
        self.network_name = os.path.basename(os.path.normpath(network_path))
        self.save_directory_path = init_results_folder(run_obj.path2curr_date_folder,self.network_name)
        self.network_dp = network_path
        self.G, self.real_communities, dictionary = read_graph_files(self.network_dp, run_obj)
        _pickle(os.path.join(self.save_directory_path, "real.communities"), self.real_communities, is_dump=True)
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
                 split_method=None, lp_list=None,
                 algorithm="louvain",
                 TimeLimit=None, benchmark_num_of_runs=1,
                 folder_name="",
                 max_mega_node_split_size=float("inf"),
                 number_runs_original_louvain=1,
                 community_file_name="community.dat",
                 network_file_name="network.dat",
                 with_comparison_to_newman_louvain=True,
                 log_to_file=True
                 ):
        if lp_list is None:
            lp_list = []
        self.algorithm = algorithm
        self.path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS,
                                                         folder_name=f"{current_time()}-{folder_name}")
        self.lp_list = lp_list
        self.split_method = split_method
        self.split_methods = {
            "mod_greedy": modularity_split_mega_node,
            "min_cut": min_cut_split_mega_node,
            "random": random_split_mega_node,
            "ilp_sub_graph": ilp_split_mega_node,
            "ilp_whole_graph": ilp_split_mega_node_whole_graph,
            "newman_whole_graph": newman_split_mega_nodes_whole_graph,
        }
        self.critical = None
        self.TimeLimit = TimeLimit
        self.benchmark_num_of_runs = benchmark_num_of_runs
        self.max_mega_node_split_size = max_mega_node_split_size
        self.number_runs_original_louvain = number_runs_original_louvain
        self.community_file_name = community_file_name
        self.network_file_name = network_file_name
        self.with_comparison = with_comparison_to_newman_louvain
        self.log_to_file = log_to_file
        self.folder_name = folder_name


# ------------------------------- Helper functions -------------------------------

def create_outputs(input_network_folder, eval_results_per_network, save_directory_path):
    # Finished
    logging.info(
        f'Finished running algos on input_network_folder= {os.path.join(save_directory_path, input_network_folder)}')
    # Create df per network
    logging.info(f'Creating DF for this network')
    data_dict = create_data_dict(eval_results_per_network)
    df = pd.DataFrame(data_dict)
    df.to_pickle(os.path.join(save_directory_path, "results.df"))
    csv_name = f"results_df-{input_network_folder}.csv"
    df.to_csv(os.path.join(save_directory_path, csv_name))
    # prompt_file(os.path.join(network_obj.save_directory_path, csv_name))


if __name__ == '__main__':
    pass
