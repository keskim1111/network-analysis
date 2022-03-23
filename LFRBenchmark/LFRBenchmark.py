import os
import subprocess
import shutil

LFR_RESULTS_FOLDER = "LFRBenchmark/Graphs"


def create_benchmark_folder(folder_name):
    if not os.path.exists(f"{LFR_RESULTS_FOLDER}/{folder_name}"):
        os.mkdir(f"{LFR_RESULTS_FOLDER}/{folder_name}")
    edges = set()
    with open("LFRBenchmark/binary_networks/network.dat") as f:
        for line in f.readlines():
            a, b = [int(i) for i in line.split()]
            edges.add((min(a, b), max(a, b)))
    with open("LFRBenchmark/binary_networks/network.dat", 'w') as f:
        for edge in edges:
            f.write(f"{edge[0]}\t{edge[1]}\n")

    os.rename("LFRBenchmark/binary_networks/network.dat", f"{LFR_RESULTS_FOLDER}/{folder_name}/network.dat")
    os.rename("LFRBenchmark/binary_networks/community.dat", f"{LFR_RESULTS_FOLDER}/{folder_name}/community.dat")
    os.rename("LFRBenchmark/binary_networks/statistics.dat", f"{LFR_RESULTS_FOLDER}/{folder_name}/statistics.dat")
    shutil.copy("LFRBenchmark/binary_networks/time_seed.dat", f"{LFR_RESULTS_FOLDER}/{folder_name}/time_seed.dat")


def generate_one_lfr_benchmark(n, mu, folder_name):
    """
    Generate random LFR benchmarks graph.
    Save all the generated graphs in ./folder_name.
    n: graph size (number of nodes)
    mu: mixed parameter
    num_of_benchmarks: number of graphs to generate per each combination
    """
    print(os.getcwd())
    os.chdir("LFRBenchmark/binary_networks")
    cmd = f"./benchmark -N {n} -k 15 -maxk 50 -mu {mu} -t1 2 -t2 1 -minc 20 -maxc 50 -on 0 -om 0"
    process = subprocess.Popen(cmd, shell=True)
    process.communicate()
    errcode = process.returncode
    process.kill()
    process.terminate()
    if errcode != 0:
        print("Please try again.")
        return
    os.chdir("../..")
    if not os.path.exists(LFR_RESULTS_FOLDER):
        os.mkdir(LFR_RESULTS_FOLDER)
    create_benchmark_folder(folder_name)


def generate_lfr_benchmarks(n_vals=(1000, 10000), mu_vals=(0.4, 0.5, 0.6), num_of_benchmarks=10):
    """
    Generate random LFR benchmarks graphs.
    For each combination of n in n_vals and mu in mu_vals, creates num_of_benchmarks random LFR graphs.
    Save all the generated graphs in ./LFR_benchmark.
    n_vals: tuple of graphs size (number of nodes)
    mu_vals: tuple of mixed parameters
    num_of_benchmarks: number of graphs to generate per each combination
    """
    for i in range(num_of_benchmarks):
        for n in n_vals:
            for mu in mu_vals:
                generate_one_lfr_benchmark(n, mu, f"{n}_{mu}_{i}")
