from pprint import pprint
from timeit import default_timer as timer

import networkx as nx

from algorithms.algorithms import louvain
from algorithms.ilp_split_community import Newman_ILP
from algorithms.ilp_newman_split_gurobi_staff_version import Newman_ILP2
from helpers import timeit
from input_networks import create_random_network


@timeit
# def trial():
#     G = create_random_network(n=40, min_community=2, max_degree=2, max_community=2, average_degree=2)
#     n = len(list(G.nodes))
#     communities = louvain(G)
#     print(f"com louvain: {len(communities)}")
#     community_dict = dict()
#     counter = 0
#     for community in communities:
#         for node in community:
#             community_dict[node] = counter
#         counter += 1
#     new_communities = partition(G, one_iteration=True, community_dict=community_dict)
#     print(f"com partition: {len(set(new_communities.values()))}")
#
#     # pprint(new_communities)

def check_split_ilp_newman_capability(n, min_community, max_degree, max_community, average_degree):
    G = create_random_network(n=n, min_community=min_community, max_degree=max_degree,
                              max_community=max_community, average_degree=average_degree)
    print(G)
    start = timer()
    c = Newman_ILP2(G)
    # c2 = Newman_ILP(G)
    print(f"Gurobi:\n {c.communities}")
    # print(f"Mine:\n {c2.communities}")
    end = timer()
    time = end - start
    print(f"split of {G.number_of_nodes()} took {time} sec")


    print(c.communities)
    return time


class RunParamInfo:
    def __init__(self, n, min_community, max_degree, max_community, average_degree):
        self.n = n
        self.min_community = min_community
        self.max_degree = max_degree
        self.max_community = max_community
        self.average_degree = average_degree


def measure_run_multi_ilp_split(runs_params_obj, num_of_runs):
    results_dict = {}
    for key, params in runs_params_obj.items():
        print(f"------Running graph with {params.n} nodes------")
        total_time = 0
        for i in range(num_of_runs):
            time = check_split_ilp_newman_capability(
                params.n,
                params.min_community,
                params.max_degree,
                params.max_community,
                params.average_degree
            )
            total_time += time
        avg_time = total_time/num_of_runs
        results_dict[key] = avg_time
        print(f"avg time for G with {key} nodes is {avg_time}")
    return results_dict



if __name__ == '__main__':
    obj1 = {
        "40": RunParamInfo(40, 4, 5, 5, 2),
    }
    obj2 = {
        "20": RunParamInfo(20, 3, 3, 5, 2),
    }
    measure_run_multi_ilp_split(obj1, 10)
