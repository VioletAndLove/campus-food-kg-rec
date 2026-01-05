import pandas as pd
import numpy as np

node_map = pd.read_pickle('rec/algo/cache/node_map.pkl')
n_users = 500          # 前 500 个节点当“用户”
n_items = len(node_map) - n_users

# 随机正交互 每人 5 正例
rng = np.random.default_rng(42)
pos = []
for u in range(n_users):
    pos.extend([(u, i) for i in rng.choice(range(n_users, len(node_map)), 5, replace=False)])
pos = pd.DataFrame(pos, columns=['user', 'item'])
pos['label'] = 1

# 负采样 1:4
neg = []
for u in range(n_users):
    neg_items = rng.choice(range(n_users, len(node_map)), 80, replace=False)
    neg.extend([(u, i) for i in neg_items])
neg = pd.DataFrame(neg, columns=['user', 'item'])
neg['label'] = 0

samples = pd.concat([pos, neg]).sample(frac=1).reset_index(drop=True)
samples[['user', 'item', 'label']].to_csv('rec/algo/cache/samples.csv', index=False)
print('样本完成：', samples.shape[0], '行')