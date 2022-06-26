import os
from pprint import pprint

from consts import FOLDER2FLOW_RESULTS, yeast_path
from flow import RunParamInfo, multi_shani_run, multi_benchmark_run, NetworkObj, run

# -------------------- Louvain ----------------------------
from helpers import init_results_folder

# TODO define default run_obj
def kesty_louvain_one_graph(path, run_obj=None):
    path2curr_date_folder = init_results_folder(FOLDER2FLOW_RESULTS)
    network_obj = NetworkObj(path2curr_date_folder, path,
                             run_obj)
    run(run_obj, network_obj)

def kesty_louvain_multiple_graphs(path, with_comparison=False, run_obj=None):
    pass


# -------------------- Neaman ----------------------------

def kesty_newman_one_graph(path, with_comparison=False, run_obj=None):
    pass


def kesty_newman_multiple_graphs(path, with_comparison=False, run_obj=None):
    pass


if __name__ == '__main__':
    # TODO add IntFeasTol to flow
    run_objects = {
        "newman-random-split-1000": RunParamInfo(algorithm="newman",
                                                 split_method="random",
                                                 lp_list=[100],
                                                 run_on_1000=True,
                                                 TimeLimit=10 * 60,
                                                 folder_name="newman-random-split-10000"
                                                 , is_shani_files=True
                                                 ),
        # "louvain-with-whole-ilp-split-1000": RunParamInfo(algorithm="louvain",
        #                                                split_method="newman_whole_graph",
        #                                                lp_list=[100],
        #                                                run_on_1000=True,
        #                                                TimeLimit=0,
        #                                                folder_name="louvain-with-newman-split-_whole_graph-1-000",
        #                                                is_shani_files=True,
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
        "louvain-with-whole-ilp-split-1000": RunParamInfo(algorithm="louvain",
                                                          split_method="newman_whole_graph",
                                                          lp_list=[100],
                                                          run_on_1000=True,
                                                          TimeLimit=0,
                                                          folder_name="louvain-with-newman-split-_whole_graph-1-000",
                                                          is_shani_files=True,
                                                          ),
        "louvain-with-sub-ilp-split-1000": RunParamInfo(algorithm="louvain",
                                                        split_method="newman_sub_graph",
                                                        lp_list=[100],
                                                        run_on_1000=True,
                                                        TimeLimit=0,
                                                        folder_name="louvain-with-newman-split-_sub_graph-1-000",
                                                        is_shani_files=True,
                                                        ),
        "louvain-with-whole-newman-split-1000": RunParamInfo(algorithm="louvain",
                                                             split_method="newman_whole_graph",
                                                             lp_list=[100],
                                                             run_on_1000=True,
                                                             TimeLimit=0,
                                                             folder_name="louvain-with-newman-split-_whole_graph-1-000",
                                                             is_shani_files=True,
                                                             ),
        # "louvain-with-newman-split-10000": RunParamInfo(algorithm="louvain",
        #                                                 split_method="newman",
        #                                                 lp_list=[100],
        #                                                 run_on_10000=True,
        #                                                 TimeLimit=10 * 60,
        #                                                 folder_name="louvain-with-newman-split-10000"
        #                                                 , is_shani_files=True
        #
        #                                                 ),

    }

    # for name, run_obj in run_objects.items():
    #     print(f"Running:\t {name} \n on shanis files with params: ")
    #     pprint(run_obj)
    #     multi_shani_run(run_obj)

    # ---------------- benchmark ----------------
    # benchmark_run_object = RunParamInfo(algorithm="newman",
    #                                     split_method="random",
    #                                     lp_list=[100],
    #                                     run_on_1000=True,
    #                                     TimeLimit=10 * 60,
    #                                     benchmark_num_of_runs=10
    #                                     )
    # multi_benchmark_run(yeast_path, benchmark_run_object)
    # ---------------- API ----------------
    run_obj_default = RunParamInfo(algorithm="louvain",
                                   split_method="random",
                                   lp_list=[100],
                                   run_on_1000=True,
                                   TimeLimit=10 * 60,
                                   folder_name="newman-random-split-10000"
                                   , is_shani_files=True
                                   )
    path1 = os.path.join(
        "C:\\Users\kimke\OneDrive\Documents\\4th_year\semeter_B\Biological_networks_sadna\\network-analysis\graphs" \
        "\Shani_graphs\\1000_0.4_0")
    kesty_louvain_one_graph(path1, run_obj=run_obj_default)

"""
idea: there are some subgraphs that ilp takes long to finish. run orpaz-neuman partially, 
but also save the final result. Then - if there is a subgraph that ilp runs for longer
than X minutes - stop the run for this subgraph and put the neuman result instead
Another option is - if it runs too long - then just add that full subgraph as 1 community and dont continue to divide it
"""
