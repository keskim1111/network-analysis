import os
from pprint import pprint
from consts import PATH2SHANIS_GRAPHS

from flow import NetworkObj, run, RunParamInfo

default_run_obj  = RunParamInfo(
        algorithm="louvain",
        split_method="random",
    )

yeast_run_obj = RunParamInfo(
        algorithm="louvain",
        split_method="random",
        network_file_name="edges.txt",
        community_file_name="clusters.txt"
    )

# -------------------- API ----------------------------

def kesty_one_graph(path, run_obj=default_run_obj):

    """
    :param path: path to folder with network and communities file
    :param run_obj: the run configurations
    :return: partition by our algorithm
    """
    try:
        network_obj = NetworkObj(path, run_obj)
        communities = run(run_obj, network_obj)
        return communities
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
    run_obj = RunParamInfo(
        algorithm="louvain",
        split_method="ilp_whole_graph",
        folder_name = "10-000 whole"
    )
    # c = kesty_one_graph(network_path2, run_obj )
    # print(c)
    d = kesty_multiple_graphs(folder_10_thousand)
    pprint(d)
