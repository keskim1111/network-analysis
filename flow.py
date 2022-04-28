import os, os.path, pandas, time, subprocess

from algorithms import louvain
from binary_files import read_binary_network_output, create_binary_network_file
from consts import C_CODE
from input_networks import create_graph_from_edge_file, read_communities_file, create_graph_from_edge_list
from helpers import init_results_folder, timeout, _pickle, timeit, create_sub_graphs_from_communities
from output_generator import generate_outputs_for_community_list
from pprint import pprint
from ilp import ILP




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

@timeit
def get_neuman_communities_shani_file(input_network_folder, results_folder="full_flow", lp_critical=1):
    """
    :param: path to folder with network for input, path to folder to save results, lp_critical - for neuman code
    :saves: saves in save_folder the binary in and out files,
             saves pickle objects of the the real community division and the algo community division.
    :returns the graph G, the real community division and the algo community division
    """
    save_folder = init_results_folder(results_folder)
    network_name = os.path.basename(input_network_folder) # shows parameters of network (num of nodes + mixing parameter)
    network_file_path = os.path.join(input_network_folder, "network.dat") # for input

    G = create_graph_from_edge_file(network_file_path) # creating graph object
    _pickle(save_folder, "edges.list", G.edges, is_dump=True) # save graph edges to file
    binary_input_fp = create_binary_network_file(G, save_folder, title=network_name, is_shanis_file=True) # converting network to binary file
    binary_output_fp = os.path.join(save_folder, f"{network_name}_{lp_critical}.out") # defining path to output file

    command = f".\cluster {binary_input_fp} {binary_output_fp} {lp_critical}" # command for neuman C code
    run_cmd(command, C_CODE)

    algo_communities = run_func_after_file_created(binary_output_fp, read_binary_network_output, {"fileName":binary_output_fp, "is_shani": True})
    real_communities = read_communities_file(os.path.join(input_network_folder, "community.dat")) # for comparing results

    # Saving the community division results
    _pickle(save_folder, "algo_communities.list", algo_communities, is_dump=True)
    _pickle(save_folder, "real_communities.list", real_communities, is_dump=True)

    return save_folder, binary_output_fp


def run_ilp_on_neuman_iterations(lp_critical_list, add_louvain=False):
    shani_graphs_dp = os.path.join(os.getcwd(), "LFRBenchmark", "Graphs")
    networks_dir = sorted(os.listdir(shani_graphs_dp), reverse=True)
    for input_network_folder in networks_dir:
        print(f'input_network_folder: {input_network_folder}')
        input_network_fp = os.path.join(shani_graphs_dp, input_network_folder)

        # Compare original neuman results to real communties
        res_fp, binary_output_fp = get_neuman_communities_shani_file(input_network_fp) # default - lp_critical==1

        real_communities = _pickle(res_fp, "real_communities.list", is_load=True)
        edges_list = _pickle(res_fp, "edges.list", is_load=True)
        G = create_graph_from_edge_list(edges_list)

        neuman_communities = _pickle(res_fp, "algo_communities.list", is_load=True)
        neuman_original_eval = generate_outputs_for_community_list(G, real_communities, neuman_communities)
        pprint(neuman_original_eval)

        for lp_critical in lp_critical_list:
            print(f'================================== LP_critical={lp_critical} ==================================')
            # Run neuman on network input
            res_fp, binary_output_fp = get_neuman_communities_shani_file(input_network_fp, lp_critical=lp_critical)

            neuman_communities = read_binary_network_output(binary_output_fp, is_shani=True)
            sub_graphs = create_sub_graphs_from_communities(G, neuman_communities)

            neuman_ilp_louvain_communities = []
            count_louvain = 0
            count_ilp = 0
            # Run neuman community results on ilp or louvain
            for i in range(len(sub_graphs)):
                g = sub_graphs[i]
                print(f'============================== Iteration {i}, subgraph size = {len(g.nodes)} ============================================')
                if add_louvain and len(g.nodes) >= 0:
                    print(f'Running louvain')
                    count_louvain += 1
                    curr_communities = louvain(g)
                else:
                    print(f'Running ilp')
                    count_ilp += 1
                    ilp_obj = ILP(g, is_networkx_graph=True)
                    curr_communities = ilp_obj.communities
                print(f'Num of communities: {len(curr_communities)}')
                neuman_ilp_louvain_communities += curr_communities

            print(f'count_louvain: {count_louvain}, count_ilp: {count_ilp}, total: {len(sub_graphs)}')
            # Evaluate results
            neuman_ilp_louvain_eval = generate_outputs_for_community_list(G, real_communities, neuman_ilp_louvain_communities)
            pprint(neuman_ilp_louvain_eval)
            pprint(neuman_original_eval)


def run_louvain_on_neuman_iterations():
    shani_graphs_dp = os.path.join(os.getcwd(), "LFRBenchmark", "Graphs")
    networks_dir = sorted(os.listdir(shani_graphs_dp), reverse=True)
    for input_network_folder in networks_dir:
        print(f'input_network_folder: {input_network_folder}')
        input_network_fp = os.path.join(shani_graphs_dp, input_network_folder)

        # Compare original neuman results to real communties
        res_fp, binary_output_fp = get_neuman_communities_shani_file(input_network_fp) # default - lp_critical==1

        real_communities = _pickle(res_fp, "real_communities.list", is_load=True)
        edges_list = _pickle(res_fp, "edges.list", is_load=True)
        G = create_graph_from_edge_list(edges_list)

        neuman_communities = _pickle(res_fp, "algo_communities.list", is_load=True)
        neuman_original_eval = generate_outputs_for_community_list(G, real_communities, neuman_communities)
        pprint(neuman_original_eval)

        sub_graphs = create_sub_graphs_from_communities(G, neuman_communities)

        # Run neuman community results on ilp or louvain
        neuman_louvain_communities = []
        for i in range(len(sub_graphs)):
            g = sub_graphs[i]
            print(f'============================== Iteration {i}, subgraph size = {len(g.nodes)} ============================================')
            curr_communities = louvain(g)
            print(f'Num of communities: {len(curr_communities)}')
            neuman_louvain_communities += curr_communities

        # Evaluate results
        neuman_ilp_louvain_eval = generate_outputs_for_community_list(G, real_communities, neuman_louvain_communities)

        print('neuman original')
        pprint(neuman_original_eval)

        print('neuman + louvain:')
        pprint(neuman_ilp_louvain_eval)





if __name__ == '__main__':
    lp_critical_list = [50, 100, 150]
    # run_ilp_on_neuman_iterations(lp_critical_list, add_louvain=True)
    run_louvain_on_neuman_iterations()
    pass





