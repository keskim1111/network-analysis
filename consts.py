"""
fp = file path
dp = dir path
"""

import os

C_CODE = os.path.join(os.getcwd(), 'neuman_orpaz_with_change')

yeast_path = os.path.join("Benchmarks", "Yeast")
arabidopsis_path = os.path.join("Benchmarks", "Arabidopsis")

edges_files = [
    os.path.join(yeast_path, "edges.txt"),
    os.path.join(arabidopsis_path, "edges.txt"),
]
clusters_files = [
    'Benchmarks\\Yeast\\clusters.txt',
    'Benchmarks\\Arabidopsis\\clusters.txt',
]
evaluation_measures = ['modularity', 'conductance', 'jaccard', 'sensitivity', 'accuracy']
msg = "The modularity result of the Algorithm is: "
community_file = "C:\\Users\\kimke\\OneDrive\\Documents\\4th year\\semeter B\\Biological networks " \
                  "sadna\\network-analysis\\LFRBenchmark\\Graphs\\1000_0.4_8\\community.dat "
edge_file = "C:\\Users\\kimke\OneDrive\\Documents\\4th year\\semeter B\\Biological networks " \
                  "sadna\\network-analysis\\LFRBenchmark\\Graphs\\1000_0.4_8\\network.dat "
yeast_edges = "C:\\Users\\kimke\\OneDrive\\Documents\\4th year\\semeter B\\Biological networks sadna\\network-analysis\\Benchmarks\\Yeast\\edges.txt"
yeast_com = "C:\\Users\\kimke\\OneDrive\\Documents\\4th year\\semeter B\\Biological networks sadna\\network-analysis\\Benchmarks\\Yeast\\clusters.txt"
Arabidopsis_edges = "C:\\Users\\kimke\\OneDrive\\Documents\\4th year\\semeter B\\Biological networks sadna\\network-analysis\\Benchmarks\\Arabidopsis\\edges.txt"

RESULTS_FOLDER = 'results'
RESULTS_FOLDER = "results"
community_file = "C:\\Users\\kimke\\OneDrive\\Documents\\4th year\\semeter B\\Biological networks " \
                 "sadna\\network-analysis\\LFRBenchmark\\Graphs\\1000_0.4_0\\community.dat "

PATH2SHANIS_GRAPHS = os.path.join(os.getcwd(), "LFRBenchmark", "Graphs")