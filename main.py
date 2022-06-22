from pprint import pprint
from flow import RunParamInfo, multi_shani_run

if __name__ == '__main__':
    # TODO add IntFeasTol to flow
    run_objects = {
        # "newman-random-split-1000": RunParamInfo(algorithm="newman",
        #                                          split_method="random",
        #                                          lp_list=[100],
        #                                          run_on_1000=True,
        #                                          TimeLimit=10 * 60,
        #                                          folder_name="newman-random-split-10000"
        #                                         ,is_shani_files=True
        #                                          ),
        "louvain-with-whole-newman-split-1000": RunParamInfo(
                                                        algorithm="louvain",
                                                       split_method="newman_whole_graph",
                                                       lp_list=[100],
                                                       run_on_1000=True,
                                                       TimeLimit=0,
                                                       folder_name="louvain-with-newman-split-_whole_graph-1-000",
                                                       is_shani_files=True,

                                                       ),
        "louvain-with-sub-newman-split-1000": RunParamInfo(algorithm="louvain",
                                                       split_method="newman_sub_graph",
                                                       lp_list=[100],
                                                       run_on_1000=True,
                                                       TimeLimit=0,
                                                       folder_name="louvain-with-newman-split-_sub_graph-1-000",
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
    for name, run_obj in run_objects.items():
        print(f"Running:\t {name} \n on shanis files with params: ")
        pprint(run_obj)
        multi_shani_run(run_obj)

    # benchmark
    # benchmark_run_object = RunParamInfo(algorithm="newman",
    #                           split_method="random",
    #                           lp_list=lp_critical_list1,
    #                           run_on_1000=True,
    #                           TimeLimit=time,
    #                           benchmark_num_of_runs= 10
    #                           )
    # multi_benchmark_run(yeast_path, benchmark_run_object)

"""
idea: there are some subgraphs that ilp takes long to finish. run orpaz-neuman partially, 
but also save the final result. Then - if there is a subgraph that ilp runs for longer
than X minutes - stop the run for this subgraph and put the neuman result instead
Another option is - if it runs too long - then just add that full subgraph as 1 community and dont continue to divide it
"""
