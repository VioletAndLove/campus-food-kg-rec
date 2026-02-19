# =============================================================================
# 功能：UCPR 推荐算法离线评测脚本，计算 HR@10 和 NDCG@10 指标
# 归属：week5-6 推荐层任务（算法原型+离线评测）
# 上游：rec/algo/cache/ent_emb.pth（训练好的实体嵌入）
#       rec/algo/cache/samples.csv（用户-物品交互样本）
#       rec/algo/ucpr_light.py（UCPR 模型定义）
# 下游：评估报告（指导模型调优，写入毕业论文实验章节）
# =============================================================================


import torch, pandas as pd
# torch: PyTorch 深度学习框架，用于加载模型和 tensor 计算，pandas: 数据处理，读取样本 CSV

import numpy as np
from sklearn.metrics import ndcg_score
# numpy: 数值计算， ndcg_score: scikit-learn 提供的 NDCG 评估指标

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# 将父目录（rec/）加入 Python 路径，以便导入 rec 包下的模块
# __file__ 是当前文件路径，os.path.dirname 获取目录名

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# 再次添加项目根目录到路径，为兼容不同运行环境

from rec.algo.ucpr_light import ent_emb, rel_emb, n_users, EMB, device
# 从 UCPR 轻量实现中导入：
# - ent_emb: 实体嵌入层（nn.Embedding），包含用户和物品的向量表示
# - rel_emb: 关系嵌入层（nn.Embedding），本代码中固定为关系0
# - n_users: 用户数量，用于划分用户嵌入和物品嵌入的边界
# - EMB: 嵌入维度（如 64/128）
# - device: 计算设备（cpu 或 cuda）

ent_emb.load_state_dict(torch.load('rec/algo/cache/ent_emb.pth'))
# 加载预训练的实体嵌入参数
# 文件路径 'rec/algo/cache/ent_emb.pth' 是相对路径，要求从项目根目录运行
# 包含所有用户和物品的嵌入向量

ent_emb.eval()
# 设置为评估模式：
# - 禁用 dropout（如果有）
# - 禁用 batch normalization 的统计更新
# - 确保嵌入向量固定，不计算梯度

samples = pd.read_csv('rec/algo/cache/samples.csv')
test = samples[samples.label == 1].copy()   # 只拿正例测

hr, ndcg = [], []   # 初始化列表，存储每个用户的 HR 和 NDCG 得分
TOPK = 10
for u in range(n_users):   # 遍历每个用户（用户 ID 从 0 到 n_users-1）
    pos_items = test[test.user == u]['item'].tolist()   # 获取用户 u 在测试集中的正例物品列表
    if not pos_items: continue
    n_items = ent_emb.weight.shape[0] - n_users   # ent_emb.weight.shape[0] 是嵌入矩阵行数（用户+物品）
    all_scores = torch.sum(ent_emb(torch.LongTensor([u] * n_items)) +   # 用户 u 的嵌入向量，复制 n_items 次
                           rel_emb(torch.LongTensor([0] * n_items)) -   # 关系嵌入，固定使用关系 0（简化版 UCPR）
                           ent_emb.weight[n_users:], dim=1)     # 所有物品的嵌入（从第 n_users 行开始），dim=1: 在嵌入维度上求和，得到每个物品的得分
    # 计算逻辑：score = ||user + relation - item|| 的负距离，或理解为 TransE 式的评分：user + relation ≈ item，值越大表示匹配度越高

    topk_items = torch.topk(all_scores, TOPK).indices.cpu().numpy() + n_users
    # torch.topk: 取分数最高的 TOPK 个
    # .indices: 获取索引（0-based 物品内部索引）
    # .cpu(): 从 GPU 移回 CPU
    # .numpy(): 转为 numpy 数组
    # + n_users: 转换为全局实体 ID（物品 ID 从 n_users 开始）

    hit = len(set(topk_items) & set(pos_items))     # 计算命中数：推荐列表与正例集合的交集大小
    hr.append(1 if hit else 0)
    # HR (Hit Ratio): 只要命中至少一个即为 1，否则为 0
    # 这里计算的是二元命中，非多命中平均

    # 简易 ndcg
    y_true = np.zeros(n_items)
    y_true[np.array(pos_items) - n_users] = 1
    y_score = all_scores.detach().numpy()
    ndcg.append(ndcg_score([y_true], [y_score], k=TOPK))
    # 计算 NDCG@10：
    # - [y_true]: 真实相关性标签（二值）
    # - [y_score]: 模型预测分数
    # - k=10: 只考虑前 10 个位置
    # 注意：这里是对全量物品计算 NDCG，非仅 TopK，可能偏低

print('HR@10 =', np.mean(hr))   # 输出平均命中率：推荐列表中至少命中一个正例的用户比例
print('NDCG@10 =', np.mean(ndcg))   # 输出平均 NDCG：考虑排序质量的归一化折损累积增益