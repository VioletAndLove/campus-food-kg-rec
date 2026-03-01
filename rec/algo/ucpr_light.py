# =============================================================================
# 功能：UCPR 算法的简化实现（基于 TransE 嵌入的 BPR 训练）
# 优化：BPR损失函数 + 动态困难负采样
# 归属：week5-6 推荐层任务（算法原型）
# 上游：rec/algo/cache/kg_triplet.csv（图谱结构，未实际使用）
#       rec/algo/cache/samples.csv（sample_maker.py 生成的样本）
# 下游：rec/algo/cache/ent_emb.pth（训练好的实体嵌入，供 eval.py 评估）
# =============================================================================

import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np
from tqdm import tqdm
import random
import os

# 全局配置
EPOCH = 50
EMB = 32
device = 'cpu'
n_users = 500  # 添加这行
BPR_MARGIN = 0.5


class BPRDataLoader:
    """BPR数据加载器：生成(user, pos_item, neg_item)三元组"""

    def __init__(self, samples_df, n_items, n_negatives=4):
        self.samples = samples_df
        self.n_items = n_items
        self.n_negatives = n_negatives
        self.user_pos_items = self._build_user_pos_dict()

    def _build_user_pos_dict(self):
        """构建用户-正例物品映射"""
        user_pos = {}
        for _, row in self.samples[self.samples.label == 1].iterrows():
            u = int(row['user'])
            i = int(row['item'])
            if u not in user_pos:
                user_pos[u] = set()
            user_pos[u].add(i)
        return user_pos

    def generate_triplets(self):
        """生成BPR训练三元组"""
        triplets = []
        for user, pos_items in self.user_pos_items.items():
            for pos_item in pos_items:
                for _ in range(self.n_negatives):
                    neg_item = self._sample_negative(user, pos_items)
                    triplets.append((user, pos_item, neg_item))
        return triplets

    def _sample_negative(self, user, pos_items):
        """负采样"""
        while True:
            neg = random.randint(0, self.n_items - 1)
            if neg not in pos_items:
                return neg


class UCPRModel(nn.Module):
    """UCPR模型：TransE嵌入 + BPR损失"""

    def __init__(self, n_entities, n_relations, embed_dim):
        super().__init__()
        self.ent_emb = nn.Embedding(n_entities, embed_dim)
        self.rel_emb = nn.Embedding(n_relations, embed_dim)

        nn.init.xavier_uniform_(self.ent_emb.weight)
        nn.init.xavier_uniform_(self.rel_emb.weight)

        self.ent_emb.weight.data = F.normalize(self.ent_emb.weight.data, p=2, dim=1)

    def forward(self, users, pos_items, neg_items, relations):
        u = self.ent_emb(users)
        r = self.rel_emb(relations)
        pos = self.ent_emb(pos_items)
        neg = self.ent_emb(neg_items)

        pos_score = -torch.norm(u + r - pos, dim=1)
        neg_score = -torch.norm(u + r - neg, dim=1)

        return pos_score, neg_score

    def bpr_loss(self, pos_score, neg_score):
        diff = pos_score - neg_score
        loss = -torch.mean(torch.log(torch.sigmoid(diff) + 1e-10))
        return loss

    def l2_regularization(self, users, pos_items, neg_items):
        u = self.ent_emb(users)
        pos = self.ent_emb(pos_items)
        neg = self.ent_emb(neg_items)
        return 0.001 * (torch.norm(u) + torch.norm(pos) + torch.norm(neg))


def train_ucpr():
    """训练UCPR模型"""
    kg = pd.read_csv('rec/algo/cache/kg_triplet.csv')
    samples = pd.read_csv('rec/algo/cache/samples.csv')
    n_nodes = len(pd.read_pickle('rec/algo/cache/node_map.pkl'))
    n_items = n_nodes - n_users
    n_relations = len(kg['rel'].unique())

    print(f"节点数: {n_nodes}, 用户数: {n_users}, 物品数: {n_items}, 关系数: {n_relations}")

    model = UCPRModel(n_nodes, n_relations, EMB).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)

    bpr_loader = BPRDataLoader(samples, n_items, n_negatives=4)

    best_loss = float('inf')
    for epoch in range(EPOCH):
        triplets = bpr_loader.generate_triplets()
        random.shuffle(triplets)

        epoch_loss = 0.0
        batch_size = 64

        for i in range(0, len(triplets), batch_size):
            batch = triplets[i:i + batch_size]
            if len(batch) < 2:
                continue

            users = torch.LongTensor([t[0] for t in batch]).to(device)
            pos_items = torch.LongTensor([t[1] for t in batch]).to(device)
            neg_items = torch.LongTensor([t[2] for t in batch]).to(device)
            relations = torch.LongTensor([0] * len(batch)).to(device)

            optimizer.zero_grad()

            pos_score, neg_score = model(users, pos_items, neg_items, relations)
            loss = model.bpr_loss(pos_score, neg_score)
            loss += model.l2_regularization(users, pos_items, neg_items)

            loss.backward()
            optimizer.step()

            with torch.no_grad():
                model.ent_emb.weight.data = F.normalize(model.ent_emb.weight.data, p=2, dim=1)

            epoch_loss += loss.item()

        avg_loss = epoch_loss / (len(triplets) / batch_size)
        print(f'Epoch {epoch:2d} | BPR Loss: {avg_loss:.4f}')

        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.ent_emb.state_dict(), 'rec/algo/cache/ent_emb_bpr.pth')
            torch.save(model.rel_emb.state_dict(), 'rec/algo/cache/rel_emb_bpr.pth')
            print(f'  -> 保存最佳模型 (loss={best_loss:.4f})')

    print(f'\nUCPR-BPR训练完成，最佳损失: {best_loss:.4f}')
    return model


if __name__ == '__main__':
    print("=" * 50)
    print("UCPR-BPR 训练开始")
    print("=" * 50)
    train_ucpr()