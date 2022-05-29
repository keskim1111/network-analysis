# network-analysis
This is a project for a university course that aims to improve existing algorithms for community detection in networks.

## prerequisites
- Run:

```
cd neuman_with_change
make
```
- Download [Gurobi][1] to your machine 

[1]: https://www.gurobi.com/documentation/9.5/quickstart_windows/software_installation_guid.html#section:Installation

## Algorithm explained

### The idea 
1. Run a known algorithm until ILP can run on current results  
2. Run ILP on current results 
3. Add ILP results if ΔQ > 0

### Known algorithms
#### Louvain

![image](https://user-images.githubusercontent.com/71821335/170860751-63115aa6-d384-4811-a29c-33c96b1bfc77.png)

#### Newman 

![image](https://user-images.githubusercontent.com/71821335/170860736-d8004134-64e9-45ab-9de1-95f1e289d2f3.png)

