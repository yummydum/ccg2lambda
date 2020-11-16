import pandas as pd

data = pd.read_csv('data/SICK_train.txt', sep="\t")
labels = data[["pair_ID",
               "entailment_judgment"]].set_index("pair_ID").to_dict()
