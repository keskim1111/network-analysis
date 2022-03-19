from networkx.generators.community import LFR_benchmark_graph

possible_mus = [0.4, 0.5, 0.6]
possible_ns = [1000, 10000]


def create_random_network(n , mu, tau1=2, tau2=1.1, average_degree=25, min_community=50):
    max_degree = int(n / 10)
    return LFR_benchmark_graph(
        n=n, tau1=tau1, tau2=tau2, mu=mu, average_degree=average_degree, max_degree=max_degree,
        min_community=min_community, max_community=int(n / 10)
    )
