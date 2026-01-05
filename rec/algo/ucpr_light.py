import torch, torch.nn as nn, torch.nn.functional as F
import pandas as pd
from tqdm import tqdm

EPOCH = 30
EMB = 32
device = 'cpu'

# 读数据
kg = pd.read_csv('rec/algo/cache/kg_triplet.csv')
samples = pd.read_csv('rec/algo/cache/samples.csv')
n_users = 50
n_nodes = len(pd.read_pickle('rec/algo/cache/node_map.pkl'))

# 简易 TransE  embedding
ent_emb = nn.Embedding(n_nodes, EMB).to(device)
rel_emb = nn.Embedding(len(kg['rel'].unique()), EMB).to(device)
optimizer = torch.optim.Adam(list(ent_emb.parameters())+list(rel_emb.parameters()), lr=1e-3)

def batch_iter(df, b=64):
    for i in range(0, len(df), b):
        yield df.iloc[i:i+b]

for epoch in range(EPOCH):
    epoch_loss = 0.
    for batch in tqdm(batch_iter(samples), leave=False):
        u = torch.LongTensor(batch.user.values).to(device)
        i = torch.LongTensor(batch.item.values).to(device)
        y = torch.FloatTensor(batch.label.values).to(device)
        r = torch.LongTensor([0]*len(batch)).to(device)  # 统一用“交互”关系 0

        score = torch.sum(ent_emb(u) + rel_emb(r) - ent_emb(i), dim=1)
        loss = F.binary_cross_entropy_with_logits(score, y)
        optimizer.zero_grad(); loss.backward(); optimizer.step()
        epoch_loss += loss.item()
    print(f'Epoch {epoch} loss {epoch_loss:.3f}')

# 保存
torch.save(ent_emb.state_dict(), 'rec/algo/cache/ent_emb.pth')
torch.save(rel_emb.state_dict(), 'rec/algo/cache/rel_emb.pth')
print('UCPR 训练完成')