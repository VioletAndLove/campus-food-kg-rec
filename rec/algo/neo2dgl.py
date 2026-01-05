from py2neo import Graph
import pandas as pd
import pickle
import os

graph = Graph("bolt://localhost:7687", auth=("neo4j", "wwj@51816888"))  # ← 改成你的密码

# 1. 抓三元组
q = """
MATCH (h)-[r]->(t)
RETURN id(h) as head_id, id(t) as tail_id, type(r) as rel
"""
df = graph.run(q).to_data_frame()

# 2. 节点重新编号 0…n-1
nodes = pd.unique(df[['head_id', 'tail_id']].values.ravel())
node_map = {n: i for i, n in enumerate(nodes)}
df['head_id'] = df['head_id'].map(node_map)
df['tail_id'] = df['tail_id'].map(node_map)

# 3. 保存
os.makedirs('rec/algo/cache', exist_ok=True)
df.to_csv('rec/algo/cache/kg_triplet.csv', index=False)
pickle.dump(node_map, open('rec/algo/cache/node_map.pkl', 'wb'))
print('导出完成：', len(nodes), '节点', len(df), '边')