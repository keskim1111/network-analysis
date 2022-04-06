from algorithms import louvain, newman
from helpers import timeit

from input_networks import create_random_network

def run():
    mu = 0.1
    tau1 = 3
    tau2 = 1.5
    average_degree = 5
    min_com = 20
    for i in range(1,11):
        n = i*1000
        G = create_random_network(n, mu, tau1, tau2, average_degree, min_com)
        print(f"run louvain with n {n}")
        com = louvain(G)
        print(f"len of com is {len(com)}")
        print(f"run newman with n {n}")
        com = newman(G)
        print(f"len of com is {len(com)}")


if __name__ == '__main__':
    run()
