import os
import subprocess

from algorithms import louvain, newman
from binary_files import read_binary_network_output, create_binary_network_file
from helpers import timeout, current_time
from input_networks import create_random_network, create_graph_from_edge_file, read_communities_file
from output_generator import generate_outputs_for_community_list
import os.path
import time
from helpers import init_results_folder

C_CODE = r'C:\Users\kimke\OneDrive\Documents\4th year\semeter B\Biological networks sadna\network-analysis\neuman_orpaz_with_change'
in_path = "g.in"
out_path = "g.out"


def run():
    mu = 0.1
    tau1 = 3
    tau2 = 1.5
    average_degree = 5
    min_com = 20
    for i in range(1, 11):
        n = i * 1000
        G = create_random_network(n, mu, tau1, tau2, average_degree, min_com)
        print(f"run louvain with n {n}")
        com = louvain(G)
        print(f"len of com is {len(com)}")
        print(f"run newman with n {n}")
        com = newman(G)
        print(f"len of com is {len(com)}")


def read_neuman_binary_files_and_print_evaluations(neuman_res_path, original_res_path):
    for file in os.listdir(neuman_res_path):
        if file.endswith("out"):
            neuman_communities = read_binary_network_output(os.path.join(neuman_res_path, file))
            for group in neuman_communities:
                for i in range(len(group)):
                    group[i] += 1
            original_communities = read_communities_file(
                os.path.join(original_res_path, file.split("-graph.out")[0], "community.dat"))
            G = create_graph_from_edge_file(os.path.join(original_res_path, file.split("-graph.out")[0], "network.dat"))
            neuman_eval = generate_outputs_for_community_list(G, original_communities, neuman_communities)
            print(f'{file}: {neuman_eval}')


@timeout(120)
def run_cmd(command, run_path):
    os.chdir(run_path)
    print(f"current path = {os.getcwd()}")
    print(f"current cmd running = {command}")
    process = subprocess.Popen(command, shell=True)
    process.communicate()
    errcode = process.returncode
    process.kill()
    process.terminate()


def run_func_after_file_created(file_created_path, func, arg):
    '''
    :param file_created_path:
    :param func:
    :param arg: a dict with key as arg name and value
    :return:
    '''
    print(" running run_func_after_file_created")
    while not os.path.exists(file_created_path):
        time.sleep(1)
    if os.path.isfile(file_created_path):
        print("file created!")
        res = func(arg)
        return res
    else:
        raise ValueError("%s isn't a file!" % file_created_path)


def full_flow(input_network_folder):
    res_folder = init_results_folder("full_flow")
    network_name = os.path.basename(input_network_folder)
    network_file_path = os.path.join(input_network_folder, "network.dat")
    community_file_path = os.path.join(input_network_folder, "community.dat")
    G = create_graph_from_edge_file(network_file_path)
    real_communities = read_communities_file(community_file_path)
    binary_input_path = create_binary_network_file(G, res_folder, title=network_name, is_shanis_file =True)
    output_file_path = os.path.join(res_folder, f"{network_name}.out")
    print("binary_input_path: ",binary_input_path)
    command = f".\cluster '{binary_input_path}' '{output_file_path}'"
    run_cmd(command, C_CODE)
    comm = run_func_after_file_created(output_file_path, read_binary_network_output, output_file_path)
    print(comm)

    pass


if __name__ == '__main__':
    # read_neuman_binary_files_and_print_evaluations( r"C:\Users\kimke\OneDrive\Documents\4th year\semeter
    # B\Biological networks sadna\network-analysis\Graphs_shani\binaries\27-04-2022--11-10-11",
    # r'C:\Users\kimke\OneDrive\Documents\4th year\semeter B\Biological networks
    # sadna\network-analysis\LFRBenchmark\Graphs') run_cmd(in_path, out_path)
    input_community_file = r"C:\Users\kimke\OneDrive\Documents\4th year\semeter B\Biological networks sadna\network-analysis\LFRBenchmark\Graphs\1000_0.4_0"
    full_flow(input_community_file)

    pass
