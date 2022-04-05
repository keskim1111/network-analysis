import pickle


class Graph:
    def __init__(self, edges_file, edges_is_list=False):
        self.nodes_range = None  # create_edges_list() updates nodes_range to be node with highest value
        self.edges_list = self.create_edges_list(edges_file, edges_is_list)
        self.num_edges = len(self.edges_list)  # maybe need to multiply by 2 ?
        self.adj_matrix = self.create_adj_matrix()
        self.degree_list = self.create_degree_list()  # maybe remove this from init bc heavy

    """
    a_ij = 1     if (i,j) in E
    a_ij = 0     else

    Assumption: nodes_range has been updated by create_edges_list()    
    """

    # TODO: in future - implement more space-efficiently (adjacency list?)
    def create_adj_matrix(self):
        adj_mat = [[0] * self.nodes_range for _ in range(self.nodes_range)]  # Initialize adjacency matrix
        for i, j in self.edges_list:
            adj_mat[i - 1][j - 1] = 1
            adj_mat[j - 1][i - 1] = 1  # make sure it is undirected graph
        return adj_mat

    def print_adj_matrix(self):
        for i in range(len(self.adj_matrix)):
            for j in range(len(self.adj_matrix)):
                print(self.adj_matrix[i][j], " ", end='')
            print('')

    # degree of node is calculated by: d_i = sum(a_il)   0<=l<=n
    def create_degree_list(self):
        degree_list = [0] * self.nodes_range  # initializing node degrees list
        for i, j in self.edges_list:
            degree_list[i - 1] += 1
            if i != j:  # not an edge to itself
                degree_list[j - 1] += 1  # Assumption: G is undirected graph - if there is (i,j) then there isn't (j,i)
        return degree_list

    def create_edges_list(self, edges_file, edges_is_list):
        max_node_val = 0

        if not edges_is_list:
            edges_list = []
            with open(edges_file) as file:
                while line := file.readline():
                    edge = tuple(line.rstrip().split())
                    edge = tuple((int(edge[0]), int(edge[1])))
                    edges_list.append(edge)
                    max_node_val = max(max_node_val, edge[0], edge[1])

        else:
            edges_list = edges_file
            # with open(edges_file, "rb") as f:
            #     edges_list = pickle.load(f)
            for i, j in edges_list:
                max_node_val = max(max_node_val, i, j)

        self.nodes_range = max_node_val + 1
        return edges_list

# G = Graph("LFRBenchmark/Graphs/1000_0.4_0/network.dat")
# G = Graph("C:/Users/97252/Documents/year_4/sadna/tests/network.dat")
# G.print_adj_matrix()
# print(G.degree_list)
# G = Graph("C://Users//97252//Documents//year_4//sadna//tests//edges_tuple.list", load_pickle=True)
# print("cool")