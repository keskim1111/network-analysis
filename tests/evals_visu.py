import os
os.chdir('C:\\Users\\97252\\Documents\\year_4\\sadna\\network-analysis')

from consts import FOLDER2FLOW_RESULTS
import pandas as pd
import pprint
import matplotlib.pyplot as plt


class df_extra:
    def __init__(self, df):
        self.df = df
        self.num_rows = df.shape[0]
        self.data_dict = {}

    def add_data_to_df(self, col_name, data):
        self.data_dict[col_name] = [data]*self.num_rows
        self.df[col_name] = data


date_folder = "17-05-2022--08-56-52"
res_dp = os.path.join(FOLDER2FLOW_RESULTS, date_folder)

dfs_list = []
for network in sorted(os.listdir(res_dp), reverse=True):
    df_fp = os.path.join(res_dp, network, "results.df")
    if network.endswith(".log") or not os.path.exists(df_fp):
        continue
    print(network)
    df = pd.read_pickle(df_fp)

    _df_extra = df_extra(df)
    _df_extra.add_data_to_df("network", network)
    _df_extra.add_data_to_df("mu", network.split("_")[1])

    dfs_list.append(df)
    # add columns to df: network, mu

df = pd.concat(dfs_list)
df.reset_index(inplace=True)
df.pop("index")

evals = ["avg_modularity", "std_modularity", "avg_jaccard", "std_jaccard"]
mus = ["all", "0.4", "0.5", "0.6"]
evals_dict = {}

for mu in mus:
    evals_dict[mu] = {}
    for _eval in evals:
        evals_dict[mu][_eval] = {}

for algo in df.algo.unique():
    for mu, evals in evals_dict.items():
        if mu == "all":
            algo_rows = df.loc[df["algo"] == algo]
        else:
            algo_rows = df.loc[df["algo"] == algo].loc[df["mu"] == mu]

        avg_modularity = algo_rows["modularity - algo"].mean()
        std_modularity = algo_rows["modularity - algo"].std()
        avg_jaccard = algo_rows["jaccard"].mean()
        std_jaccard = algo_rows["jaccard"].std()

        if algo.startswith("Neumann-ILP"):
            algo = algo.split("-")[1] + algo.split("-")[2]
            algo = algo.replace("ILP", "NLP")

        evals["avg_modularity"][algo] = avg_modularity
        evals["std_modularity"][algo] = std_modularity
        evals["avg_jaccard"][algo] = avg_jaccard
        evals["std_jaccard"][algo] = std_jaccard

#     algos_results[algo] = {"avg_modularity": avg_modularity, "std_modularity": std_modularity,
#                            "avg_jaccard": avg_jaccard, "std_jaccard": std_jaccard}
pprint.pprint(evals_dict)

for mu, mu_evals in evals_dict.items():
    for eval_name, eval_data in mu_evals.items():
        fig, ax = plt.subplots()
        ax.set_title(f'{eval_name}, mu={mu}')
        x = eval_data.values()
        y = eval_data.keys()
        ax.plot(y, x)