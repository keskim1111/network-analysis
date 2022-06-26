import os
from pprint import pprint
from flow import RunParamInfo, NetworkObj, run


# -------------------- API ----------------------------

# TODO define default run_obj
def kesty_one_graph(path, run_obj):
    """
    :param path: path to folder with network and communities file
    :param run_obj: the run configurations
    :return: partition by our algorithm
    """
    network_obj = NetworkObj(path, run_obj)
    communities = run(run_obj, network_obj)
    return communities


def kesty_louvain_multiple_graphs(path_of_graphs, run_obj):
    '''
    :param path_of_graphs: path to folder with folders of networks and communities files
    :param run_obj: the run configurations
    :return: dictionary with network name and its partition
    '''
    folders_dict = {}
    for input_network_folder in sorted(os.listdir(path_of_graphs), reverse=True):
        print(f"------- Running {input_network_folder} graph ------------")
        communities = kesty_one_graph(os.path.join(path_of_graphs, input_network_folder), run_obj)
        folders_dict[input_network_folder] = communities
    return folders_dict


if __name__ == '__main__':

    # ------------------------ API -------------------------
    run_obj_default = RunParamInfo(
        algorithm="louvain",
        split_method="random",
    )

    shani_folder_paths = os.path.join(
        "C:\\Users\kimke\OneDrive\Documents\\4th_year\semeter_B\Biological_networks_sadna\\network-analysis\graphs\Shani_graphs")
    network_path = os.path.join(shani_folder_paths, "1000_0.4_0")

    # kesty_one_graph(path1, run_obj=run_obj_default)
    kesty_louvain_multiple_graphs(shani_folder_paths, run_obj_default)
