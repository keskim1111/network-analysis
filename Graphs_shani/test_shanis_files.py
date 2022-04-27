import os

from algorithms import newman
from binary_files import create_binary_network_file
from consts import RESULTS_FOLDER
from helpers import current_time
from input_networks import create_random_network, create_graph_from_edge_file
from datetime import datetime

run_folder_names = ["run_1", "run_2", "run_3"]
graphs_folder_names = ["1000_0.4_1", "1000_0.5_4", "1000_0.6_8", "10000_0.4_6", "10000_0.5_2"]


def create_output_folder(folder_name, parent_folder=RESULTS_FOLDER):
    path = f"{parent_folder}/{folder_name}"
    if not os.path.exists(f"{parent_folder}"):
        os.mkdir(f"{parent_folder}")
    os.mkdir(path)

    return path


def write_to_file(file, content):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    line = f"[{current_time}]: {content}\n"
    print(line)
    with open(file, "a") as f:
        f.write(line)
    return file


def run_shani_files():
    output_path = create_output_folder(f"results_{current_time()}")
    write_to_file(f"{output_path}\logs", "Started run")
    for run_folder in run_folder_names:
        for graphs_folder in graphs_folder_names:
            n, mu, num = graphs_folder.split("_")
            network_graph = create_random_network(int(n), float(mu))
            write_to_file(f"{output_path}\logs", f"####### running {graphs_folder}")
            community_path = rf"{run_folder}\{graphs_folder}\community.dat"
            shani_graph = create_graph_from_edge_file(community_path)
            write_to_file(f"{output_path}\logs", "created shani_graph")
            write_to_file(f"{output_path}\logs", "created network_graph")
            d = {"network": network_graph, "shani": shani_graph}
            for graph in d.keys():
                try:
                    result = newman(d[graph])
                    write_to_file(f"{output_path}\logs",
                                  f"ran newman on {graphs_folder} of {graph} with results:\n {result}")
                except Exception as e:
                    write_to_file(f"{output_path}\logs", f"timeout of {graph}")
                    continue
    pass


def create_binarys():
    path = create_output_folder(current_time(),"binaries")
    for run_folder in run_folder_names:
        for graphs_folder in graphs_folder_names:
            community_path = rf"{run_folder}\{graphs_folder}\community.dat"
            shani_graph = create_graph_from_edge_file(community_path)
            create_binary_network_file(shani_graph, path, graphs_folder)
    print("done")


def create_binarys_network():
    path = create_output_folder(current_time(),"binaries_network")
    network_graph = create_random_network(int(1000), float(0.4))
    create_binary_network_file(network_graph, path, "binaries_network")
    print("done")

if __name__ == '__main__':
    # run_shani_files()
    create_binarys()
    # create_binarys_network()
