import os
from pprint import pprint
from consts import PATH2SHANIS_GRAPHS, yeast_path

from flow import NetworkObj, run, RunParamInfo

default_run_obj = RunParamInfo(
    algorithm="louvain",
    split_method="random",
    console_log_level= "info"
)

yeast_run_obj = RunParamInfo(
    algorithm="louvain",
    split_method="ilp_whole_graph",
    TimeLimit=60,
    network_file_name="edges.txt",
    community_file_name="clusters.txt",
    console_log_level = "debug",
    folder_name="ddd"

)


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
        communities = run(run_obj, network_obj)
        original_nodes_communities = convert_to_original_nodes(communities, network_obj)
        return original_nodes_communities
    except Exception as e:
        print("There is a problem to run the program")
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
            print(f"------- Running {input_network_folder} graph ------------")
            communities = kesty_one_graph(os.path.join(path_of_graphs, input_network_folder), run_obj)
            folders_dict[input_network_folder] = communities
        return folders_dict
    except Exception as e:
        print("There is a problem to run the program")
        raise e


if __name__ == '__main__':
    folder_10_thousand = os.path.join(PATH2SHANIS_GRAPHS, "10_000")
    folder_1_thousand = os.path.join(PATH2SHANIS_GRAPHS, "1000")
    run_obj = RunParamInfo(
        lp_list=[100],
        algorithm="louvain",
        split_method="newman_whole_graph",
        folder_name = "newman-split_subgraph-1000"
    )
    # yeast_run_obj = RunParamInfo(
    #         algorithm="louvain",
    #         split_method="newman_whole_graph",
    #         network_file_name="edges.txt",
    #         community_file_name="clusters.txt",
    #         folder_name="newman-split-yeast"
    # )
    # c = kesty_one_graph(yeast_path, yeast_run_obj)
    # print(c)
    d = kesty_multiple_graphs(folder_1_thousand, run_obj)
    pprint(d)
