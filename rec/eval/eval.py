import torch, pandas as pd
import numpy as np
from sklearn.metrics import ndcg_score
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from rec.algo.ucpr_light import ent_emb, rel_emb, n_users, EMB, device

ent_emb.load_state_dict(torch.load('rec/algo/cache/ent_emb.pth'))
ent_emb.eval()

samples = pd.read_csv('rec/algo/cache/samples.csv')
test = samples[samples.label == 1].copy()   # 只拿正例测

hr, ndcg = [], []
TOPK = 10
for u in range(n_users):
    pos_items = test[test.user == u]['item'].tolist()
    if not pos_items: continue
    n_items = ent_emb.weight.shape[0] - n_users
    all_scores = torch.sum(ent_emb(torch.LongTensor([u] * n_items)) +
                           rel_emb(torch.LongTensor([0] * n_items)) -
                           ent_emb.weight[n_users:], dim=1)
    topk_items = torch.topk(all_scores, TOPK).indices.cpu().numpy() + n_users
    hit = len(set(topk_items) & set(pos_items))
    hr.append(1 if hit else 0)
    # 简易 ndcg
    y_true = np.zeros(n_items)
    y_true[np.array(pos_items) - n_users] = 1
    y_score = all_scores.detach().numpy()
    ndcg.append(ndcg_score([y_true], [y_score], k=TOPK))

print('HR@10 =', np.mean(hr))
print('NDCG@10 =', np.mean(ndcg))