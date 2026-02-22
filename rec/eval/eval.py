# =============================================================================
# 功能：UCPR 推荐算法离线评测脚本，计算 HR@10 和 NDCG@10 指标
# 归属：week5-6 推荐层任务（算法原型+离线评测）
# 上游：rec/algo/cache/ent_emb.pth（训练好的实体嵌入）
#       rec/algo/cache/samples.csv（用户-物品交互样本）
#       rec/algo/ucpr_light.py（UCPR 模型定义）
# 下游：评估报告（指导模型调优，写入毕业论文实验章节）
# =============================================================================

import torch, pandas as pd
import numpy as np
from sklearn.metrics import ndcg_score
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from rec.algo.ucpr_light import ent_emb, rel_emb, n_users, EMB, device

# 加载训练好的模型
ent_emb.load_state_dict(torch.load('rec/algo/cache/ent_emb.pth', map_location=device))
ent_emb.eval()

# 读取测试样本
samples = pd.read_csv('rec/algo/cache/samples.csv')
test = samples[samples.label == 1].copy()

# 评估指标计算
hr, ndcg = [], []
TOPK = 10

for u in range(n_users):
    pos_items = test[test.user == u]['item'].tolist()
    if not pos_items:
        continue

    n_items = ent_emb.weight.shape[0] - n_users

    # 修复：使用负距离作为评分，与训练时一致
    user_vec = ent_emb(torch.LongTensor([u] * n_items))
    rel_vec = rel_emb(torch.LongTensor([0] * n_items))
    item_vecs = ent_emb.weight[n_users:]

    all_scores = -torch.norm(user_vec + rel_vec - item_vecs, dim=1)

    # 取 topk，indices 是 0-based 的物品内部索引
    topk_indices = torch.topk(all_scores, TOPK).indices.cpu().numpy()
    # 转换为全局实体 ID：加 n_users（500）
    topk_items = topk_indices + n_users

    hit = len(set(topk_items) & set(pos_items))
    hr.append(1 if hit else 0)

    # NDCG 计算
    y_true = np.zeros(n_items)
    # pos_items 是全局 ID，转为内部索引
    pos_indices = np.array(pos_items) - n_users
    y_true[pos_indices] = 1
    y_score = all_scores.detach().numpy()
    ndcg.append(ndcg_score([y_true], [y_score], k=TOPK))

print(f'HR@10 = {np.mean(hr):.4f}')
print(f'NDCG@10 = {np.mean(ndcg):.4f}')