"""
fp = file path
dp = dir path
"""

import os


C_CODE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'algorithms/newman_lp_critical')
C_CODE_SPLIT = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'algorithms/newman_split_new')
benchmark_base_path = os.path.join("Graphs" , "Benchmark")

yeast_path = os.path.join(benchmark_base_path, "Yeast")
arabidopsis_path = os.path.join(benchmark_base_path, "Arabidopsis")

edges_files = [
    os.path.join(yeast_path, "edges.txt"),
    os.path.join(arabidopsis_path, "edges.txt"),
]
CLUSTER_FILE_TXT = "clusters.txt"
clusters_files = [
    os.path.join(yeast_path, CLUSTER_FILE_TXT),
    os.path.join(arabidopsis_path, CLUSTER_FILE_TXT)
]
evaluation_measures = ['modularity', 'conductance', 'jaccard', 'sensitivity', 'accuracy']
msg = "The modularity result of the Algorithm is: "

RESULTS_FOLDER = 'results'
default_lp_list=[100]

PATH2SHANIS_GRAPHS = os.path.join(os.getcwd(), "Graphs", "Shani_graphs")
PATH2BENCHMARKS_GRAPHS = benchmark_base_path
FOLDER2FLOW_RESULTS = os.path.join(os.getcwd(), RESULTS_FOLDER, "full_flow")