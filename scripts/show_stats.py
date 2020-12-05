import pickle
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set()

stat_path = Path('data/stat.pkl')
with stat_path.open(mode='rb') as f:
    stat = pickle.load(f)

threshold = '2793'
df = pd.DataFrame([[k, v]
                   for k, v in stat['goal_n'].items() if str(k) <= threshold],
                  columns=['pairID', 'subgoal_len'])
print(df['subgoal_len'].value_counts())

df = pd.DataFrame(
    [[k, v] for k, v in stat['readable_n'].items() if str(k) <= threshold],
    columns=['pairID', 'subgoal_len'])
print(df['subgoal_len'].value_counts())

breakpoint()