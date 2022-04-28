import os, pickle
import subprocess
from binary_files import read_binary_network_output, create_binary_network_file
from consts import C_CODE
from input_networks import create_graph_from_edge_file, read_communities_file
import os.path
import time
from helpers import init_results_folder, timeout, write_to_file, _pickle
from output_generator import generate_outputs_for_community_list
from pprint import pprint


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


def run_func_after_file_created(file_created_path, func, args):
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
        print(f"file created in {file_created_path}")
        res = func(**args)
        return res
    else:
        raise ValueError("%s isn't a file!" % file_created_path)


def get_neuman_communities_shani_file(input_network_folder, results_folder="full_flow", lp_critical=1):
    res_folder = init_results_folder(results_folder)
    network_name = os.path.basename(input_network_folder)
    network_file_path = os.path.join(input_network_folder, "network.dat")
    community_file_path = os.path.join(input_network_folder, "community.dat")
    G = create_graph_from_edge_file(network_file_path)
    real_communities = read_communities_file(community_file_path)
    binary_input_path = create_binary_network_file(G, res_folder, title=network_name, is_shanis_file=True)
    output_file_path = os.path.join(res_folder, f"{network_name}.out")
    command = f".\cluster {binary_input_path} {output_file_path} {lp_critical}"
    run_cmd(command, C_CODE)
    algo_communities = run_func_after_file_created(output_file_path, read_binary_network_output, {"fileName":output_file_path, "is_shani": True})
    _pickle(res_folder, "algo_communities.list", algo_communities, is_dump=True)
    _pickle(res_folder, "real_communities.list", real_communities, is_dump=True)

    return G, real_communities, algo_communities


if __name__ == '__main__':
    input_folder = os.path.join(os.getcwd(), "LFRBenchmark","Graphs","1000_0.4_0")
    G, real_communities, algo_communities = get_neuman_communities_shani_file(input_folder)
    neuman_original_eval = generate_outputs_for_community_list(G, real_communities, algo_communities)
    pprint(neuman_original_eval)

