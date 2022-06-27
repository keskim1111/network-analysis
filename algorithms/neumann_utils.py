import os, subprocess
from helpers import timeit, timeout
from consts import C_CODE, C_CODE_SPLIT
import time
from utils.binary_files import read_binary_network_output, create_binary_communities_file


@timeout(120)
def run_cmd(command, run_path):
    print(f"Run path is {run_path}")
    print(f"current path = {os.getcwd()}")
    os.chdir(run_path)
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
def get_neumann_communities(save_dp, network_name, binary_input_fp, lp_critical=1):
    binary_output_fp = os.path.join(save_dp,
                                    f"{network_name}_{lp_critical}.out")  # defining path to output file
    command = f".\cluster {binary_input_fp} {binary_output_fp} {lp_critical}"  # command for Neumann C code
    print(f"C_CODE: {C_CODE}")
    run_cmd(command, C_CODE)
    neumann_communities = run_func_after_file_created(binary_output_fp, read_binary_network_output,
                                                      {"fileName": binary_output_fp})

    return neumann_communities


@timeit
def split_communities_with_newman(save_dp, network_name, binary_graph_input_fp, communities):
    binary_output_fp = os.path.join(save_dp,
                                    f"{network_name}.out")  # defining path to output file

    binary_communities_input_fp = create_binary_communities_file(communities, save_dp)
    command = f".\cluster {binary_graph_input_fp} {binary_communities_input_fp} {binary_output_fp}"  # command for Neumann C code
    print(f"C_CODE: {C_CODE_SPLIT}")
    run_cmd(command, C_CODE_SPLIT)
    newman_communities = run_func_after_file_created(binary_output_fp, read_binary_network_output,
                                                      {"fileName": binary_output_fp})

    return newman_communities
