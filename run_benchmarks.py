from input_networks import *
from algorithms import *
from output_generator import *

#

G = create_random_network(250, 0.1, 3, 1.5, 5, 20)
partition = create_partition(G)

# visualization
create_visual_graph(G, partition)


"""
- understand benchmark parameters function
- add function that calculates modularity of benchmark graph https://github.com/taynaud/python-louvain
- compare modularity to louvain and neuman
- create function that summarizes results when running examples
- measure time
- 

"""
