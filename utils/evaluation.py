import logging

import math


# Helpers
import networkx as nx


def calc_jaccard(clusters_dict1, clusters_dict2):
    """
    calculates jaccard score between clusters_dict1 and clusters_dict2
    :param clusters_dict1, clusters_dict2: dictionary where the key is the cluster's index
           and the values are the points indexes that are members of the cluster
    :return: the jaccard score
    """
    couples1 = all_possible_couples(clusters_dict1)
    couples2 = all_possible_couples(clusters_dict2)
    intersection = intersection_size(couples1, couples2)
    union = len(couples1) + len(couples2) - intersection
    return intersection / union


def intersection_size(set1, set2):
    """
    :return: how many items intersects between set1 and set2
    """
    intersection_size = 0
    # checking which set is smaller in order to go over it efficiently
    size1 = len(set1)
    size2 = len(set2)
    shorter_set = set1 if size1 < size2 else set2
    longer_set = set2 if size1 < size2 else set1

    for item in shorter_set:
        if item in longer_set:
            intersection_size += 1
    return intersection_size


def all_possible_couples(clusters_dict):
    """
    :return: return all possible couples whithin points that are in the same cluster, for every cluster
             for example, if we have 2 clusters and the dict looks like: {1: [2,3], 2: [4,5,6]}
             the function returns a set: {(2,3),(4,5),(5,6),(4,6)}
    """
    all_possible_couples_set = set()
    for cluster in clusters_dict.values():
        all_possible_couples_set.update(combinations(cluster))
    return all_possible_couples_set


def combinations(lst):
    """
    :return: this func returns all n choose 2 combinations of items in list
    """
    couples_set = set()
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            couples_set.add(tuple(sorted([lst[i], lst[j]])))
    return couples_set


def create_clusters_dict(communities_list):
    '''
    :param communities_list:
    :return: a dictionary with number as key and cluster members in a list as a value
    '''
    curr_dict = dict()
    i = 0
    for community in communities_list:
        curr_dict[i] = list(community)
        i += 1
    return curr_dict


# Internal
def calc_modularity_nx(G, communities, weight=None):
    try:
        mod = nx.algorithms.community.modularity(G, communities, weight=weight)
        logging.debug(f"Running NetworkX modularity function on: {G}, modularity={mod}")
        return mod
    except Exception as e:
        logging.error(e)
        raise e


# TODO: make sure it make sense to not normalize (1/m)
def calc_modularity_manual(G, communities: [[]],weight=None):
    """
    :param G: networkx graph
    :param communities: list of lists of communities (nodes)
    :return:
            Q =  \sum_{ij} ( A_{ij} - {k_ik_j}/{2m})
    """
    sum_modularity = 0
    for i in range(len(communities)):
        nodes_list = communities[i]
        # print("nodes_list: \n",nodes_list)
        # print("nodes_list: \n",type(nodes_list))
        # print("nodes_list[0]: \n",nodes_list[0])
        # print("nodes_list[0]: \n",type(nodes_list[0]))
        # print(G.nodes(data=True))

        num_of_nodes = len(nodes_list)
        m = G.size(weight=weight)
        adj = G.adj
        # print(f'adj: {adj}')
        # print("dict(dict(adj)[0].items()).get(16)  ",dict(dict(adj)[0].items()).get(16))
        cur_modularity = 0 # [sum_ij] (a_ij - (d_i * d_j)/2m)
        for node_range_1 in range(num_of_nodes):
            for node_range_2 in range(node_range_1):  # i < j
                j = nodes_list[node_range_1]
                i = nodes_list[node_range_2]
                # TODO this is problamatic
                # print(f'i:\n {i}')
                # print(f'adj:\n {adj}')
                # print(f'type(adj):\n {type(adj)}')
                # print(f'adj.get(i):\n {adj.get(i)}')
                # print(f'adj.get(i).items(j):\n {adj.get(i).get(j)}')
                if dict(dict(adj)[i].items()).get(j) is not None:
                    a_ij = dict(dict(adj)[i].items())[j].get("weight", 1)
                else:
                    a_ij = 0

                cur_modularity += a_ij - (G.degree(i,weight=weight) * G.degree(j,weight=weight)) / (2 * m)
        sum_modularity += cur_modularity
    return sum_modularity


# TODO make sure it is the same as in requiremants
# https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.cuts.conductance.html
def conductance(G, cluster):
    '''
    measurement for each cluster - how many edges are in the cluster vs. put of it
    :return:
    '''
    return nx.conductance(G, cluster)


def graph_conductance(G, communities):
    '''
    :param G:
    :param communities:
    :return: conductance score of a graph
    '''
    res = sum([conductance(G, cluster) for cluster in communities])
    return 1 - (1 / len(communities) * res)


# External
def jaccard(communities1, communities2):
    clusters_dict1 = create_clusters_dict(communities1)
    clusters_dict2 = create_clusters_dict(communities2)
    return calc_jaccard(clusters_dict1, clusters_dict2)


def known_community_sensitivity(known_community, candidate_communities):
    max_intersection = 0
    for candidate_community in candidate_communities:
        max_intersection = max(intersection_size(known_community, candidate_community), max_intersection)
    return max_intersection


def graph_sensitivity(known_communities, candidate_communities):
    I = 0
    N = 0
    for knwon_community in known_communities:
        N += len(knwon_community)
        I += known_community_sensitivity(knwon_community, candidate_communities)
    return I / N


# TODO make more efficient and make sure is right
def ppv_max_per_community(candidate_community, known_communities):
    max_res = 0
    for known_community in known_communities:
        int_with_current = intersection_size(candidate_community, known_community)
        max_res = max(max_res, int_with_current)
    return max_res


def graph_PPV(known_communities, candidate_communities):
    PPV = 0
    int_all_total = 0
    for candidate_community in candidate_communities:
        int_with_all = sum([intersection_size(candidate_community, com) for com in known_communities])
        int_all_total += int_with_all
        PPV += ppv_max_per_community(candidate_community, known_communities)
    try:
        result = PPV / int_all_total
        return result
    except ZeroDivisionError:
        print(f"Error {ZeroDivisionError}")
        return 0


def graph_accuracy(known_communities, candidate_communities):
    ppv = graph_PPV(known_communities, candidate_communities)
    sn = graph_sensitivity(known_communities, candidate_communities)
    return math.sqrt(sn * ppv)