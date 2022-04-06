import functools
import time
from datetime import datetime


def timeit(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        print('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsed_time * 1_000)))
        return result

    return new_func


def current_time():
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y--%H-%M-%S")
    return dt_string


def adjacency_matrix(G):
    num_of_nodes = G.number_of_nodes()
    adj_mat = [[0] * num_of_nodes for _ in range(num_of_nodes)]  # Initialize adjacency matrix
    for i, j in G.edges:
        adj_mat[i][j] = 1
        adj_mat[j][i] = 1  # make sure it is undirected graph
    return adj_mat
