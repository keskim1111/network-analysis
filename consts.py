"""
fp = file path
dp = dir path
"""

import os

C_CODE = os.path.join(os.getcwd(), 'neuman_orpaz_with_change')

yeast_path = os.path.join("Benchmark", "Yeast")
arabidopsis_path = os.path.join("Benchmark", "Arabidopsis")

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

PATH2SHANIS_GRAPHS = os.path.join(os.getcwd(), "Benchmark", "Graphs")
FOLDER2FLOW_RESULTS = os.path.join(os.getcwd(),RESULTS_FOLDER, "full_flow")