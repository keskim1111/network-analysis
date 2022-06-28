![image](https://user-images.githubusercontent.com/71821335/176128096-19008ad5-2e37-4ebd-9cd1-a0a93e9b373b.png)

## Motivation

This project is as part as a workshop in [Analysis of Biological Networks](http://www.cs.tau.ac.il/~roded/courses/bnet21.html), instructed by Prof. Roded Sharan and Shani Jacobson.    
The workshop aims to improve existing algorithms for community detection in networks.

## Contents

- [Network-analysis Project](#network-analysis-project)
    + [Motivation](#motivation)
    + [Contents](#contents)
  * [Installation](#installation)
    + [How to use](#how-to-use)
      - [1. NetworkX graph as input](#1-networkx-graph-as-input)
      - [2. Graph file as input](#2-graph-file-as-input)
    + [Description](#description)
    + [The idea](#the-idea)
    + [Known algorithms](#known-algorithms)
      - [Louvain](#louvain)
      - [Newman](#newman)
    + [References](#references)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>


## Installation

1. Clone the repository
   ```bash
   $ git clone https://github.com/keskim1111/network-analysis.git
   ```
2. Make sure to have a C compiler on your computer and run:
    ```bash
    cd algorithms/newman_lp_critical
    make
    cd algorithms/newman_split
    make
    ```

3. Download [Gurobi][1] to your machine 
## How to use

### Quick start

```python
from api import kesty_one_graph, kesty_multiple_graphs

# for single graph
graph_path = "graphs/Shani_graphs/1000_0.4_0"
communities = kesty_one_graph(graph_path)
# for multiple graphs
graphs_path = "graphs/Shani_graphs"
communities_dictionary = kesty_multiple_graphs(graphs_path)

```
We expect the graph path to include two files with the following  formats:

- communities.dat 
  ```
  1 0
  2 0
  3 0
  4 1
  5 1
  6 1
  ```
- network.dat 
  ```
  1 2
  2 3
  1 3
  4 5
  4 6 
  5 6
  ```
### Adding Run configurations
You can play with the run object arguments

| argument     | values      | purpose  | default value|
| :------------ |   :---:       | --------: | --------: |
| `algorithm`        | `"louvain","newman"`         | The updated algorithm chosen to run   |`"louvain"`|
| `split_method`         | `"mod_greedy","min_cut","random","ilp_sub_graph","ilp_whole_graph","newman_whole_graph"`         | split   |`"newman_whole_graph"`|
| `lp_list`         | Test2         | `Los Angeles`   ||
| `TimeLimit`         | Test2         | `Los Angeles`   ||
| `folder_name`         | Test2         | `Los Angeles`   ||
| `max_mega_node_split_size`         | Test2         | `Los Angeles`   ||
| `number_runs_original_louvain`         | Test2         | `Los Angeles`   ||
| `community_file_name`         | Test2         | `Los Angeles`   ||
| `network_file_name`         | Test2         | `Los Angeles`   ||
| `with_comparison_to_newman_louvain`         | Test2         | `Los Angeles`   ||
| `log_to_file`         | Test2         | `Los Angeles`   ||
| `console_log_level`         | Test2         | `Los Angeles`   ||


````python
from api import kesty_one_graph
from flow import RunParamInfo

yeast_run_obj = RunParamInfo(
  algorithm="louvain",
  split_method="random",
  network_file_name="edges.txt",
  community_file_name="clusters.txt"
)
graph_path = "graphs\\Benchmark\\Yeast"
communities = kesty_one_graph(graph_path, yeast_run_obj)

````
  
  


[1]: https://www.gurobi.com/documentation/9.5/quickstart_windows/software_installation_guid.html#section:Installation

## Description


### The idea 
1. Run a known algorithm until ILP can run on current results  
2. Run ILP on current results 
3. Add ILP results if ΔQ > 0

### Known algorithms
#### Louvain

![שרטוט לוביין עם פיצול](https://user-images.githubusercontent.com/71821335/176128435-c736d328-7a77-4853-b4dc-340041141f3d.jpg)

#### Newman 

![image](https://user-images.githubusercontent.com/71821335/170860736-d8004134-64e9-45ab-9de1-95f1e289d2f3.png)


## References


[1] Newman, M. E. J. (2006). Modularity and community structure in networks. Proceedings of the National Academy of Sciences of the United States of America, 103(23), 8577–82. https://doi.org/10.1073/pnas.0601602103

[2]  Blondel, Vincent D; Guillaume, Jean-Loup; Lambiotte, Renaud; Lefebvre, Etienne (9 October 2008). "Fast unfolding of communities in large networks". Journal of Statistical Mechanics: Theory and Experiment. 2008  doi:[10.1088/1742-5468/2008/10/P10008](10.1088/1742-5468/2008/10/P10008)
