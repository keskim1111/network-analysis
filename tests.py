import os

from algorithms import louvain, newman
from binary_files import read_binary_network_output
from helpers import timeit

from input_networks import create_random_network, create_graph_from_edge_file, read_communities_file
from output_generator import generate_outputs_for_community_list


def run():
    mu = 0.1
    tau1 = 3
    tau2 = 1.5
    average_degree = 5
    min_com = 20
    for i in range(1,11):
        n = i*1000
        G = create_random_network(n, mu, tau1, tau2, average_degree, min_com)
        print(f"run louvain with n {n}")
        com = louvain(G)
        print(f"len of com is {len(com)}")
        print(f"run newman with n {n}")
        com = newman(G)
        print(f"len of com is {len(com)}")



def read_neuman_and_compare(neuman_res_path, original_res_path):
    for file in os.listdir(neuman_res_path):
        if file.endswith("out"):
            neuman_communities = read_binary_network_output(os.path.join(neuman_res_path, file))
            for group in neuman_communities:
                for i in range(len(group)):
                    group[i]+=1
            original_communities = read_communities_file(os.path.join(original_res_path, file.split("-graph.out")[0], "community.dat"))
            G = create_graph_from_edge_file(os.path.join(original_res_path, file.split("-graph.out")[0], "network.dat"))
            neuman_eval = generate_outputs_for_community_list(G, original_communities, neuman_communities)
            print(f'{file}: {neuman_eval}')

if __name__ == '__main__':
    read_neuman_and_compare(r"C:\Users\kimke\OneDrive\Documents\4th year\semeter B\Biological networks sadna\network-analysis\Graphs_shani\binaries\27-04-2022--11-10-11",
                            r'C:\Users\kimke\OneDrive\Documents\4th year\semeter B\Biological networks sadna\network-analysis\LFRBenchmark\Graphs')

