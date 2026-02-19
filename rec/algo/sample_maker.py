# =============================================================================
# 功能：生成用户-物品交互样本（正例+负采样），用于训练推荐模型
# 归属：week5-6 推荐层任务（训练数据准备）
# 上游：rec/algo/cache/node_map.pkl（neo2dgl.py 生成的节点映射）
# 下游：rec/algo/cache/samples.csv（ucpr_light.py 的训练数据）
# =============================================================================

import pandas as pd
import numpy as np

node_map = pd.read_pickle('rec/algo/cache/node_map.pkl')    # 加载节点映射，获取总节点数
n_users = 500          # 假设前 500 个节点当“用户”⚠️
n_items = len(node_map) - n_users   # 物品数 = 总节点 - 用户数


# 随机正交互 每人 5 正例
rng = np.random.default_rng(42) # 创建随机数生成器，种子 42 保证可复现
pos = []
for u in range(n_users):
    pos.extend([(u, i) for i in rng.choice(range(n_users, len(node_map)), 5, replace=False)])   # 为每个用户 u 随机选 5 个物品作为正例
    # range(n_users, len(node_map)): 物品 ID 范围（假设物品索引在用户之后）
    # replace=False: 不放回抽样，避免重复
pos = pd.DataFrame(pos, columns=['user', 'item'])
pos['label'] = 1
# 构建正例 DataFrame，标记 label=1

# 负采样 1:4
neg = []
for u in range(n_users):
    neg_items = rng.choice(range(n_users, len(node_map)), 80, replace=False)
    # 每人采 80 个负例（80 = 5正例 × 16，但后续只取部分？⚠️）
    neg.extend([(u, i) for i in neg_items])
neg = pd.DataFrame(neg, columns=['user', 'item'])
neg['label'] = 0
# 构建负例 DataFrame，标记 label=0

samples = pd.concat([pos, neg]).sample(frac=1).reset_index(drop=True)
samples[['user', 'item', 'label']].to_csv('rec/algo/cache/samples.csv', index=False)
# 保存为 CSV，供训练使用
# 注意：这里负例远多于正例（80 vs 5），但 BPR 损失通常只需 1:1 或 1:4


print('样本完成：', samples.shape[0], '行')