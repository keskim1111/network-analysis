import os
from pprint import pprint

from consts import FOLDER2FLOW_RESULTS, yeast_path
from flow import RunParamInfo, multi_shani_run, NetworkObj, run


# -------------------- API ----------------------------

# TODO define default run_obj
def kesty_one_graph(path, run_obj=None):
    '''
    :param path: path to folder with network and communities file
    :param run_obj: the run configurations
    :return: partition by our algorithm
    '''
    network_obj = NetworkObj(path, run_obj)
    communities = run(run_obj, network_obj)
    return communities


def kesty_louvain_multiple_graphs(path_of_graphs, run_obj=None):
    folders_dict = {}
    for input_network_folder in sorted(os.listdir(path_of_graphs), reverse=True):
        communities = kesty_one_graph(os.path.join(path_of_graphs, input_network_folder), run_obj=None)
        folders_dict[input_network_folder] = communities
    return folders_dict


if __name__ == '__main__':
    # TODO add IntFeasTol to flow
    run_objects = {
        # "newman-random-split-1000": RunParamInfo(algorithm="newman",
        #                                          split_method="random",
        #                                          lp_list=[100],
        #                                          run_on_1000=True,
        #                                          TimeLimit=10 * 60,
        #                                          folder_name="newman-random-split-10000"
        #                                          ),
        # "louvain-with-whole-ilp-split-1000": RunParamInfo(algorithm="louvain",
        #                                                split_method="newman_whole_graph",
        #                                                lp_list=[100],
        #                                                run_on_1000=True,
        #                                                TimeLimit=0,
        #                                                folder_name="louvain-with-newman-split-_whole_graph-1-000",
        #
        #                                                ),
        # "louvain-with-sub-ilp-split-1000": RunParamInfo(algorithm="louvain",
        #                                                split_method="newman_sub_graph",
        #                                                lp_list=[100],
        #                                                run_on_1000=True,
        #                                                TimeLimit=0,
        #                                                folder_name="louvain-with-newman-split-_sub_graph-1-000",
        #                                                is_shani_files=True,
        #                                                ),
        # "louvain-with-whole-ilp-split-1000": RunParamInfo(algorithm="louvain",
        #                                                   split_method="newman_whole_graph",
        #                                                   lp_list=[100],
        #                                                   run_on_1000=True,
        #                                                   TimeLimit=0,
        #                                                   folder_name="louvain-with-newman-split-_whole_graph-1-000",
        #                                                   ),
        # "louvain-with-sub-ilp-split-1000": RunParamInfo(algorithm="louvain",
        #                                                 split_method="newman_sub_graph",
        #                                                 lp_list=[100],
        #                                                 run_on_1000=True,
        #                                                 TimeLimit=0,
        #                                                 folder_name="louvain-with-newman-split-_sub_graph-1-000",
        #                                                 ),
        # "louvain-with-whole-newman-split-1000": RunParamInfo(algorithm="louvain",
        #                                                      split_method="newman_whole_graph",
        #                                                      lp_list=[100],
        #                                                      run_on_1000=True,
        #                                                      TimeLimit=0,
        #                                                      folder_name="louvain-with-newman-split-_whole_graph-1-000",
        #                                                      ),
        # "louvain-with-newman-split-10000": RunParamInfo(algorithm="louvain",
        #                                                 split_method="newman",
        #                                                 lp_list=[100],
        #                                                 run_on_10000=True,
        #                                                 TimeLimit=10 * 60,
        #                                                 folder_name="louvain-with-newman-split-10000"
        #
        #                                                 ),

    }

    # ---------------- API ----------------
    run_obj_default = RunParamInfo(
        algorithm="newman",
        split_method="random",
        lp_list=[100],
        TimeLimit=10 * 60,
        folder_name="newman_random_split"
    )
    path1 = os.path.join(
        "C:\\Users\kimke\OneDrive\Documents\\4th_year\semeter_B\Biological_networks_sadna\\network-analysis\graphs""\Shani_graphs\\1000_0.4_0")

    kesty_one_graph(path1, run_obj=run_obj_default)
