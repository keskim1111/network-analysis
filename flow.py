import os
from timeit import default_timer as timer
import pandas as pd
import logging
from algorithms.algorithms import louvain, newman
from algorithms.modified_louvain import modified_louvain_communities
from algorithms.utils import convert_mega_nodes_to_communities, split_mega_nodes, modularity_split_mega_node, \
    min_cut_split_mega_node, random_split_mega_node, newman_split_mega_node
from binary_files import create_binary_network_file
from consts import PATH2SHANIS_GRAPHS, FOLDER2FLOW_RESULTS, yeast_path, arabidopsis_path, PATH2BENCHMARKS_GRAPHS
from evaluation import calc_modularity_manual, calc_modularity_nx
from input_networks import create_graph_from_edge_file, read_communities_file, create_graph_from_edge_list
from helpers import init_results_folder, _pickle, prompt_file, current_time, save_str_graph_in_good_format
from logger import setup_logger
from algorithms.ilp import ILP
from output_generator import save_and_eval, create_data_dict
from algorithms.Neumann import get_neumann_communities


# ------------------------------- Louvain -------------------------------

def multi_benchmark_run(run_obj):
    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True):
        if run_obj.run_on_10000 and "10000" in input_network_folder:
            if run_obj.algorithm == "louvain":
                run_with_comparison_louvain(input_network_folder, run_obj
                                            )
        if run_obj.run_on_1000 and "1000_" in input_network_folder:
            if run_obj.algorithm == "louvain":
                run_with_comparison_louvain(input_network_folder, run_obj)


# add try catch to run ilp .. bc of out of memory
def run_with_comparison_louvain(input_network_folder,
                                run_obj,
                                withTimeLimit=False,
                                TimeLimit=0,
                                ):
    network_obj, eval_results_per_network = run_setup(run_obj.path2curr_date_folder,
                                                      input_network_folder)
    logging.info(f'===================== Running: Louvain networkx =======================')
    run_louvain(network_obj.save_directory_path, eval_results_per_network, network_obj.G, network_obj.real_communities)
    logging.info(f'===================== Running: Louvain Changed networkx =======================')
    run_louvain_with_change(TimeLimit, withTimeLimit, eval_results_per_network,
                            network_obj.save_directory_path,
                            network_obj.G,
                            network_obj.real_communities,
                            run_obj,
                            input_network_folder=input_network_folder,
                            lp_critical_values=run_obj.lp_list
                            )
    create_outputs(input_network_folder, eval_results_per_network, network_obj.save_directory_path)
    logging.info(f'eval_results_per_network={eval_results_per_network}')


def run_ilp_on_louvain(G, withTimeLimit=False, TimeLimit=0):
    '''
    :param G: graph with MEGA nodes
    :return: communites
    '''
    nodes_list = list(G.nodes)
    mod_mega_graph_divided = calc_modularity_nx(G, [[n] for n in nodes_list], weight="weight")
    mod_mega_graph_full = calc_modularity_nx(G, [nodes_list], weight="weight")
    logging.info(f'============Trying to run ILP============')
    if withTimeLimit:
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


# ------------------------------- Newman -------------------------------

# TODO: add column of average subgraph size (that was run by ILP).
def multi_run_newman(lp_criticals, lp_timelimit):
    done_dict = {0.4: 0, 0.5: 0, 0.6: 0}
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)
    for input_network_folder in sorted(os.listdir(PATH2SHANIS_GRAPHS), reverse=True):
        if "10000" in input_network_folder:
            for mu in done_dict.keys():
                if str(mu) in input_network_folder and done_dict[mu] <= 3:  # run up to 3 runs per mu
                    done_dict[mu] += 1
                    print(done_dict)
                    print(input_network_folder)
                    run_with_comparison_newman(input_network_folder, path2curr_date_folder, lp_criticals, lp_timelimit)


def run_with_comparison_newman(input_network_folder,
                               path2curr_date_folder,
                               lp_critical_values,
                               lp_timelimit):
    network_obj, eval_results_per_network = run_setup(path2curr_date_folder, input_network_folder)

    logging.info(f'===================== Running: Louvain networkx =======================')
    run_louvain(network_obj.save_directory_path, eval_results_per_network, network_obj.G, network_obj.real_communities)
    logging.info(f'===================== Running: Neumann C =======================')
    run_newman(eval_results_per_network,
               lp_critical_values,
               lp_timelimit,
               network_obj.save_directory_path,
               network_obj.network_name,
               network_obj.binary_input_fp,
               network_obj.G,
               network_obj.real_communities,
               is_shani=True
               )
    logging.info(f'===================== Running: Neumann C changed=======================')

    run_newman_with_change(
        eval_results_per_network,
        lp_critical_values,
        lp_timelimit,
        network_obj.save_directory_path,
        network_obj.network_name,
        network_obj.binary_input_fp,
        network_obj.G,
        network_obj.real_communities,
        is_shani=True
    )
    # Finished
    create_outputs(input_network_folder, eval_results_per_network, network_obj.save_directory_path)
    logging.info(f'eval_results_per_network={eval_results_per_network}')


def run_ilp_on_neumann(G,
                       neumann_communities: [list],
                       lp_critical: int,
                       withTimeLimit=False,
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
    ilp_results_obj = RunParamInfo(communities=final_communities)
    ilp_results_obj.critical = lp_critical
    ilp_results_obj.num_coms_divided = num_communities_divided_by_ilp
    ilp_results_obj.num_coms_skipped = num_communities_skipped_by_ilp
    return ilp_results_obj


# ------------------------------- Benchmarks ( yeast and arabidopsis ) -------------------------------

def run_on_benchmark(lp_critical_values,
                     path,
                     benchmark_name,
                     withTimeLimit=False,
                     TimeLimit=0,
                     split_method=None,
                     runs=10):
    # TODO more runs
    eval_results_per_network = []  # Save all final results in this list (for creating df later)
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)
    logging.info(f"Benchmark name is: {benchmark_name}")
    network_obj = NetworkObj(path2curr_date_folder, benchmark_name, is_benchmark=True)

    setup_logger(os.path.join(path2curr_date_folder, benchmark_name), log_to_file=True)
    logging.info(f'Starting to run algos on {benchmark_name}')
    logging.error(f"path is {path}!!")

    # add alone nodes
    # nodes_set = set(G.nodes)
    # print(nodes_set)
    # nodes_set2 = set()
    # for c in real_communities:
    #     for n in c:
    #         nodes_set2.add(n)
    # if nodes_set != nodes_set2:
    #     print(f"G nodes:{len(nodes_set)}")
    #     print(f"real nodes:{len(nodes_set2)}")
    #     print(nodes_set2 - nodes_set)

    # print(f"G:\n{G},\nreal_communities:\n{real_communities}")
    run_obj = RunParamInfo(split_method=split_method)

    logging.info(f'===================== Running: Neumann C =======================')
    binary_input_fp = create_binary_network_file(network_obj.G, network_obj.save_directory_path,
                                                 title=benchmark_name)  # converting network to binary file
    run_newman(eval_results_per_network,
               lp_critical_values,
               TimeLimit,
               network_obj.save_directory_path,
               benchmark_name,
               binary_input_fp,
               network_obj.G,
               network_obj.real_communities,
               is_shani=False
               )
    logging.info(f'===================== Running: Louvain networkx =======================')
    run_louvain(network_obj.save_directory_path, eval_results_per_network, network_obj.G, network_obj.real_communities)

    logging.info(f'===================== Running: Louvain Changed networkx =======================')
    run_louvain_with_change(TimeLimit,
                            withTimeLimit,
                            eval_results_per_network,
                            network_obj.save_directory_path,
                            network_obj.G,
                            network_obj.real_communities,
                            run_obj,
                            input_network_folder=os.path.join(benchmark_name),
                            lp_critical_values=lp_critical_values)

    logging.info(f'eval_results_per_network={eval_results_per_network}')
    create_outputs(benchmark_name, eval_results_per_network, network_obj.save_directory_path)


# ------------------------------- SNAP ( yeast and arabidopsis ) -------------------------------

def run_on_snap(lp_critical_values,
                path,
                withTimeLimit=False,
                TimeLimit=0,
                benchmark_name="yeast",
                split_method=None,
                runs=10):
    # TODO more runs
    eval_results_per_network = []  # Save all final results in this list (for creating df later)
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)
    logging.info(f"Benchmark name is: {benchmark_name}")
    save_directory_path = init_results_folder(path2curr_date_folder, benchmark_name)

    setup_logger(os.path.join(path2curr_date_folder, benchmark_name), log_to_file=True)
    logging.info(f'Starting to run algos on {benchmark_name}')
    logging.error(f"path is {path}!!")
    edges_list = _pickle(os.path.join(path, "edges.list"), is_load=True)
    G = create_graph_from_edge_list(edges_list)
    real_communities = _pickle(os.path.join(path, "clusters.list"), is_load=True)
    run_obj = RunParamInfo(split_method=split_method)

    logging.info(f'===================== Running: Neumann C =======================')
    binary_input_fp = create_binary_network_file(G, save_directory_path,
                                                 title=benchmark_name)  # converting network to binary file
    run_newman(eval_results_per_network,
               lp_critical_values,
               TimeLimit,
               save_directory_path,
               benchmark_name,
               binary_input_fp,
               G,
               real_communities,
               is_shani=False
               )
    logging.info(f'===================== Running: Louvain networkx =======================')
    run_louvain(save_directory_path, eval_results_per_network, G, real_communities)

    logging.info(f'===================== Running: Louvain Changed networkx =======================')
    run_louvain_with_change(TimeLimit,
                            withTimeLimit,
                            eval_results_per_network,
                            save_directory_path,
                            G,
                            real_communities,
                            run_obj,
                            input_network_folder=os.path.join(benchmark_name),
                            lp_critical_values=lp_critical_values)

    logging.info(f'eval_results_per_network={eval_results_per_network}')
    create_outputs(benchmark_name, eval_results_per_network, save_directory_path)


# ------------------------------- Helper classes -------------------------------
class NetworkObj:
    def __init__(self, main_dp, network_name, is_shanis_file=False,
                 is_benchmark=False, run_param_obj=None,
                 ):
        self.network_name = network_name
        self.save_directory_path = init_results_folder(main_dp, f"{network_name}")
        if is_shanis_file:
            self.network_dp = os.path.join(PATH2SHANIS_GRAPHS, self.network_name)
            self.real_communities = read_communities_file(os.path.join(self.network_dp, "community.dat"))
            self.G = create_graph_from_edge_file(os.path.join(self.network_dp, "network.dat"))  # creating graph object
        if is_benchmark:
            path = os.path.join(PATH2BENCHMARKS_GRAPHS, self.network_name)
            self.network_dp = path
            self.G, self.real_communities, d = save_str_graph_in_good_format(path)
        _pickle(os.path.join(self.save_directory_path, "real.communities"), self.real_communities, is_dump=True)
        self.binary_input_fp = create_binary_network_file(self.G, self.save_directory_path,
                                                          title=self.network_name,
                                                          is_shanis_file=is_shanis_file)  # converting network to binary file
        self.multi_obj = run_param_obj


class RunParamInfo:
    def __init__(self, communities=None, mega_communities=None,
                 split_method=None, lp_list=None, run_on_1000=False,
                 run_on_10000=False, algorithm="louvain"):
        if lp_list is None:
            lp_list = []
        self.algorithm = algorithm
        self.path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)
        self.run_on_1000 = run_on_1000
        self.run_on_10000 = run_on_10000
        self.lp_list = lp_list
        self.split_method = split_method
        self.split_methods = {
            "mod_greedy": modularity_split_mega_node,
            "min_cut": min_cut_split_mega_node,
            "random": random_split_mega_node,
            "newman": newman_split_mega_node
        }

        # move
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


def run_louvain(save_directory_path, eval_results_per_network, G, real_communities):
    start = timer()
    louvain_communities = louvain(G)
    end = timer()
    logging.warning(f'Finished runnning regular Louvain: num communties = {len(louvain_communities)}')
    save_and_eval(save_directory_path, eval_results_per_network, G,
                  real_communities,
                  new_communities=louvain_communities, algo="Louvain", time=end - start)


def run_newman(eval_results_per_network,
               lp_criticals,
               lp_timelimit,
               save_directory_path,
               network_name,
               binary_input_fp,
               G,
               real_communities,
               is_shani=False):
    start = timer()
    neumann_communities = get_neumann_communities(save_directory_path,
                                                  network_name,
                                                  binary_input_fp,
                                                  is_shani=is_shani)
    end = timer()
    save_and_eval(save_directory_path, eval_results_per_network, G,
                  real_communities,
                  new_communities=neumann_communities,
                  algo="Newman",
                  time=end - start)


def run_newman_with_change(eval_results_per_network,
                           lp_criticals,
                           lp_timelimit,
                           save_directory_path,
                           network_name,
                           binary_input_fp,
                           G,
                           real_communities,
                           is_shani=False):
    for lp_critical in lp_criticals:
        logging.info(f'=================== LP_critical={lp_critical} -Time limit ===============')
        start = timer()
        neuman_com_partial_run = get_neumann_communities(save_directory_path,
                                                         network_name,
                                                         binary_input_fp,
                                                         lp_critical=lp_critical,
                                                         is_shani=is_shani)
        TimeLimit = lp_timelimit  # in seconds
        newman_ilp_results_obj = run_ilp_on_neumann(G,
                                                    neuman_com_partial_run,
                                                    lp_critical=lp_critical,
                                                    withTimeLimit=True,
                                                    TimeLimit=TimeLimit)
        end = timer()
        newman_ilp_results_obj.runtime = end - start
        save_and_eval(
            save_directory_path,
            eval_results_per_network, G,
            real_communities,
            new_communities=newman_ilp_results_obj.communities,
            algo=f'NLP-{lp_critical}-TL-{TimeLimit}',
            time=newman_ilp_results_obj.runtime,
            extra_evals=newman_ilp_results_obj
        )


def run_louvain_with_change(TimeLimit,
                            withTimeLimit,
                            eval_results_per_network,
                            save_directory_path,
                            G,
                            real_communities,
                            run_obj,
                            lp_critical_values,
                            input_network_folder):
    for critical in lp_critical_values:
        logging.warning(f'lp_critical={critical}, timelimit={TimeLimit}')
        start = timer()
        iterations_number, mega_graph = modified_louvain_communities(G, num_com_bound=critical)
        run_obj.critical = critical
        logging.warning(f'Finished runnning regular Louvain: num nodes mega graph = {mega_graph.number_of_nodes()}')
        try:
            logging.info(f'about to run_ilp_on_louvain')
            # split mega graph
            if run_obj.split_method is not None:
                mega_graph = split_mega_nodes(G, mega_graph, critical, run_obj)
                logging.warning(f'Splitted nodes. num of nodes in mega is {mega_graph.number_of_nodes()}')
            # regular run
            number_of_mega_nodes = mega_graph.number_of_nodes()
            run_obj.number_of_mega_nodes = number_of_mega_nodes
            mega_communities_partition = run_ilp_on_louvain(mega_graph,
                                                            withTimeLimit=withTimeLimit,
                                                            TimeLimit=TimeLimit)
            curr_communities = convert_mega_nodes_to_communities(mega_graph, mega_communities_partition)
            end = timer()
            run_obj.communities = curr_communities
            run_obj.iterations_number = iterations_number
            run_obj.runtime = end - start
            logging.warning(f"Finished running ILP Louvain: num of final communities: {len(curr_communities)}")
            save_and_eval(
                save_directory_path,
                eval_results_per_network,
                G,
                real_communities,
                new_communities=curr_communities,
                algo=f'LLP-{critical}',
                time=end - start,
                extra_evals=run_obj)
            logging.info(f'------ success running ilp on louvain, lp_critical={critical}')
        except Exception as e:
            logging.info(
                f'run_one_louvain didnt work on {input_network_folder}, lp_critical={critical}')
            logging.error(e)
            raise e
    create_outputs(input_network_folder, eval_results_per_network, save_directory_path)
    logging.info(f'eval_results_per_network={eval_results_per_network}')


def run_setup(path2curr_date_folder, input_network_folder):
    # define logger output ##############
    setup_logger(os.path.join(path2curr_date_folder, input_network_folder))
    logging.info(f'Starting to run algos on input_network_folder= {input_network_folder}')
    eval_results_per_network = []  # Save all final results in this list (for creating df later)
    network_obj = NetworkObj(path2curr_date_folder, input_network_folder, is_shanis_file=True)
    return network_obj, eval_results_per_network


if __name__ == '__main__':
    lp_critical_list1 = [100]
    time = 10 * 60
    lp_critical_for_10001 = [100]
    lp_critical_for_100001 = [100]
    # multi_run_newman(lp_critical_list1, time)

    # run_object = RunParamInfo(algorithm="louvain",
    #                           split_method="random",
    #                           lp_list=lp_critical_list1,
    #                           run_on_1000=True,
    #                           )
    # multi_benchmark_run(run_object)

    #### one run louvain
    # path2curr_date_folder1 = os.path.join(
    #     'C:\\Users\\kimke\\OneDrive\\Documents\\4th_year\\semeter_B\\Biological_networks_sadna\\network-analysis\\results\\full_flow\\',
    #     current_time())
    # input_network_folder1 = '1000_0.6_9'
    # run_one_louvain(input_network_folder1, path2curr_date_folder1, lp_critical_list1, is_split_mega_nodes=True)
    # run_one_newman(input_network_folder1, path2curr_date_folder1, lp_critical_values=lp_critical_list1, lp_timelimit=time)

    run_on_benchmark(lp_critical_list1,path=yeast_path, benchmark_name="yeast", split_method="random")
    pass
