# Network-analysis

---
This project is as part as a workshop in [Analysis of Biological Networks](http://www.cs.tau.ac.il/~roded/courses/bnet21.html), instructed by Prof. Roded Sharan and Shani Jacobson.    
The workshop aims to improve existing algorithms for community detection in networks.

## Contents

---
- [Network-analysis](#network-analysis)
  * [Prerequisites](#prerequisites)
  * [Usage](#usage)
  * [Description](#description)
    + [The idea](#the-idea)
    + [Known algorithms](#known-algorithms)
      - [Louvain](#louvain)
      - [Newman](#newman)
  * [References](#references)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

## Installation

---

1. Clone the repository
   ```bash
   $ git clone https://github.com/keskim1111/network-analysis.git
   ```
2. Make sure to have a C compiler on your computer 
    ```bash
    cd algorithms/neuman_with_change_c
    make
    ```

4. Download [Gurobi][1] to your machine 
## Usage

---

[1]: https://www.gurobi.com/documentation/9.5/quickstart_windows/software_installation_guid.html#section:Installation

## Description

---

### The idea 
1. Run a known algorithm until ILP can run on current results  
2. Run ILP on current results 
3. Add ILP results if ΔQ > 0

### Known algorithms
#### Louvain

![image](https://user-images.githubusercontent.com/71821335/170860751-63115aa6-d384-4811-a29c-33c96b1bfc77.png)

#### Newman 

![image](https://user-images.githubusercontent.com/71821335/170860736-d8004134-64e9-45ab-9de1-95f1e289d2f3.png)

## References

---

[1] Newman, M. E. J. (2006). Modularity and community structure in networks. Proceedings of the National Academy of Sciences of the United States of America, 103(23), 8577–82. https://doi.org/10.1073/pnas.0601602103

[2]  Blondel, Vincent D; Guillaume, Jean-Loup; Lambiotte, Renaud; Lefebvre, Etienne (9 October 2008). "Fast unfolding of communities in large networks". Journal of Statistical Mechanics: Theory and Experiment. 2008  doi:[10.1088/1742-5468/2008/10/P10008](10.1088/1742-5468/2008/10/P10008)
