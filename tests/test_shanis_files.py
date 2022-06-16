from algorithms.algorithms import newman
from utils.binary_files import create_binary_network_file
from helpers import current_time, write_to_file
from input_networks import create_random_network, create_graph_from_edge_file

run_folder_names = ["run_1", "run_2", "run_3"]
graphs_folder_names = ["1000_0.4_1", "1000_0.5_4", "1000_0.6_8", "10000_0.4_6", "10000_0.5_2"]





def run_shani_files():
    output_path = create_output_folder2(f"results_{current_time()}")
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
    path = create_output_folder2(current_time(), "binaries")
    for run_folder in run_folder_names:
        for graphs_folder in graphs_folder_names:
            community_path = rf"{run_folder}\{graphs_folder}\community.dat"
            shani_graph = create_graph_from_edge_file(community_path)
            create_binary_network_file(shani_graph, path, graphs_folder)
    print("done")


def create_binarys_network():
    path = create_output_folder2(current_time(), "binaries_network")
    network_graph = create_random_network(int(1000), float(0.4))
    create_binary_network_file(network_graph, path, "binaries_network")
    print("done")

if __name__ == '__main__':
    # run_shani_files()
    create_binarys()
    # create_binarys_network()
