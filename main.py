import logging
import os
from pprint import pprint

from flow import NetworkObj, run, RunParamInfo
from utils.logger import setup_logger

default_run_obj = RunParamInfo(
    algorithm="louvain",
    split_method="newman_whole_graph",
)

yeast_run_obj = RunParamInfo(
    algorithm="louvain",
    split_method="ilp_whole_graph",
    TimeLimit=60,
    network_file_name="edges.txt",
    community_file_name="clusters.txt",
    # console_log_level = "debug",
    folder_name="ara"

)


# -------------------- API ----------------------------

def convert_to_original_nodes(communities, network_obj):
    original_nodes_communities = []
    for c in communities:
        community = []
        for node in c:
            community.append(network_obj.network_dictionary[node])
        original_nodes_communities.append(community)
    return original_nodes_communities


def kesty_one_graph(path, run_obj=default_run_obj):
    """
    :param path: path to folder with network and communities file
    :param run_obj: the run configurations
    :return: partition by our algorithm
    """
    try:
        run_obj.init_results_folder()
        network_obj = NetworkObj(path, run_obj)
        setup_logger(os.path.join(network_obj.save_directory_path, network_obj.network_name),
                     log_to_file=run_obj.log_to_file, console_log_level=run_obj.console_log_level)
        logging.info(f"Running changed {run_obj.algorithm} algo on {network_obj.network_name}")
        communities = run(run_obj, network_obj)
        original_nodes_communities = convert_to_original_nodes(communities, network_obj)
        return original_nodes_communities
    except Exception as e:
        logging.error("There is a problem to run the program")
        raise e


def kesty_multiple_graphs(path_of_graphs, run_obj=default_run_obj):
    """
    :param path_of_graphs: path to folder with folders of networks and communities files
    :param run_obj: the run configurations
    :return: dictionary with network name and its partition
    """
    folders_dict = {}
    try:
        for input_network_folder in sorted(os.listdir(path_of_graphs), reverse=True):
            logging.debug(f"------- Running {input_network_folder} graph ------------")
            communities = kesty_one_graph(os.path.join(path_of_graphs, input_network_folder), run_obj)
            folders_dict[input_network_folder] = communities
        return folders_dict
    except Exception as e:
        logging.error("There is a problem to run the program")
        raise e


if __name__ == '__main__':
    shani_folder_paths = os.path.join(
        "C:\\Users\kimke\OneDrive\Documents\\4th_year\semeter_B\Biological_networks_sadna\\network-analysis\graphs\Shani_graphs")
    network_path = os.path.join("C:\\Users\kimke\OneDrive\Documents\\4th_year\semeter_B\Biological_networks_sadna\\network-analysis\graphs\Shani_graphs\\1000\\1000_0.4_0")
    network_path2 = os.path.join("C:\\Users\kimke\Desktop\\10000_0.6_2")
    yeast = "graphs\\Benchmark\\Yeast"
    Arabidopsis = "graphs\\Benchmark\\Arabidopsis"

    run_obj = RunParamInfo(
        algorithm="louvain",
        split_method="ilp_whole_graph",
        folder_name="1000 whole"
    )
    # c = kesty_one_graph(yeast, yeast_run_obj)
    # c = kesty_one_graph(Arabidopsis, yeast_run_obj)
    # c = kesty_one_graph(network_path, default_run_obj)
    # print(c)
    d = kesty_multiple_graphs("C:\\Users\\kimke\\Desktop\\temp")
    pprint(d)
