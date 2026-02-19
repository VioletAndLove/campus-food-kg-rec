# =============================================================================
# 功能：UCPR 算法的简化实现（基于 TransE 嵌入的 BPR 训练）
# 归属：week5-6 推荐层任务（算法原型）
# 上游：rec/algo/cache/kg_triplet.csv（图谱结构，未实际使用）
#       rec/algo/cache/samples.csv（sample_maker.py 生成的样本）
# 下游：rec/algo/cache/ent_emb.pth（训练好的实体嵌入，供 eval.py 评估）
# =============================================================================

import torch, torch.nn as nn, torch.nn.functional as F
import pandas as pd
from tqdm import tqdm
# tqdm: 进度条库，显示训练进度

EPOCH = 30  # 训练轮数
EMB = 32    # 嵌入维度，对应 UCPR 论文中的 d
device = 'cpu'  # 强制使用 CPU（无 GPU 环境或小规模数据）

# 读数据
kg = pd.read_csv('rec/algo/cache/kg_triplet.csv')
# 读取知识图谱三元组（本文件未实际使用 kg，仅加载）
# ⚠️ 潜在扩展：可加入图谱正则化或路径采样
samples = pd.read_csv('rec/algo/cache/samples.csv') # 读取训练样本（user, item, label）
n_users = 500
n_nodes = len(pd.read_pickle('rec/algo/cache/node_map.pkl'))  # 总节点数（用户+物品+其他实体如 Tag, Ingredient）


# 简易 TransE  embedding
ent_emb = nn.Embedding(n_nodes, EMB).to(device)
# 实体嵌入层：所有节点（用户、物品、标签、食材等）共享同一嵌入空间
# shape: (n_nodes, 32)，每行是一个节点的 32 维向量
rel_emb = nn.Embedding(len(kg['rel'].unique()), EMB).to(device) # 关系嵌入层：每种关系类型一个嵌入向量
optimizer = torch.optim.Adam(list(ent_emb.parameters())+list(rel_emb.parameters()), lr=1e-3)
# Adam 优化器，联合优化实体和关系嵌入
# lr=1e-3: 学习率 0.001

def batch_iter(df, b=64):
    for i in range(0, len(df), b):
        yield df.iloc[i:i+b]

for epoch in range(EPOCH):
    epoch_loss = 0.
    for batch in tqdm(batch_iter(samples), leave=False):    # tqdm 包裹批次迭代器，显示进度条，leave=False: 完成后清除进度条，避免刷屏
        u = torch.LongTensor(batch.user.values).to(device)  # 用户 ID 转为 LongTensor（嵌入层索引要求整数）
        i = torch.LongTensor(batch.item.values).to(device)  # 物品 ID
        y = torch.FloatTensor(batch.label.values).to(device)    # 标签（1=正例，0=负例），用于 BCE 损失
        r = torch.LongTensor([0]*len(batch)).to(device)  # 统一用“交互”关系 0
        # ⚠️ 与 UCPR 论文差异：UCPR 使用路径推理，此处仅为 TransE 评分

        score = torch.sum(ent_emb(u) + rel_emb(r) - ent_emb(i), dim=1)
        # TransE 评分函数：s = u + r - i（向量加减）
        # torch.sum(..., dim=1): 在嵌入维度求和，得到标量分数
        # 物理意义：分数越高表示 u + r ≈ i 越成立，即用户-关系-物品匹配度越高

        loss = F.binary_cross_entropy_with_logits(score, y)
        # 二元交叉熵损失（带 sigmoid）：
        # loss = -[y*log(sigmoid(s)) + (1-y)*log(1-sigmoid(s))]
        # 正例（y=1）希望 s 越大越好，负例（y=0）希望 s 越小越好

        optimizer.zero_grad()    # 清空梯度（避免累积）
        loss.backward()     # 反向传播计算梯度
        optimizer.step()    # 更新参数
        epoch_loss += loss.item()   # 累加批次损失（.item() 提取标量值）
    print(f'Epoch {epoch} loss {epoch_loss:.3f}')

# 保存
torch.save(ent_emb.state_dict(), 'rec/algo/cache/ent_emb.pth')  # 保存实体嵌入参数（仅权重，不包含模型结构）
torch.save(rel_emb.state_dict(), 'rec/algo/cache/rel_emb.pth')  # 保存关系嵌入参数（虽然实际只用到关系 0）

print('UCPR 训练完成')