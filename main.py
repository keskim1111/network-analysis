from input_networks import *
from algorithms import *
from output_generator import *
possible_mus = [0.4, 0.5, 0.6]
possible_ns = [1000, 10000]

def create_example():
    G = create_random_network(250, 0.1, 3, 1.5, 5, 20)
    partition = create_partition(G)
    figure = create_visual_graph(G, partition)


create_example()



