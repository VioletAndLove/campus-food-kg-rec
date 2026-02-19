# =============================================================================
# 功能：将 Neo4j 图数据库中的知识图谱导出为 DGL/PyG 可用的三元组格式
# 归属：week5-6 推荐层任务（数据预处理，为 GNN 训练准备）
# 上游：Neo4j 数据库（json2neo4j.py 构建的校园美食 KG）
# 下游：rec/algo/cache/kg_triplet.csv（供 ucpr_light.py 训练使用）
# =============================================================================

from py2neo import Graph
import pandas as pd
import pickle
import os

graph = Graph("bolt://localhost:7687", auth=("neo4j", "wwj@51816888"))  # 连接 Neo4j 数据库

# 1. 抓三元组
q = """
MATCH (h)-[r]->(t)
RETURN id(h) as head_id, id(t) as tail_id, type(r) as rel
"""
# Cypher 查询：匹配所有头节点-关系->尾节点模式
# id(h): Neo4j 内部节点 ID（全局唯一，但可能不连续）
# type(r): 关系类型字符串，如 "HAS_TAG", "CONTAINS"

df = graph.run(q).to_data_frame()
# 执行查询并转为 pandas DataFrame
# 结果列：head_id（头节点 ID）, tail_id（尾节点 ID）, rel（关系类型）


# 2. 节点重新编号 0…n-1
nodes = pd.unique(df[['head_id', 'tail_id']].values.ravel())  #提取所有唯一节点id，展平为一维数组
node_map = {n: i for i, n in enumerate(nodes)}  #创建映射字典：原生id->新id：0,1,2,3,4，
df['head_id'] = df['head_id'].map(node_map)
df['tail_id'] = df['tail_id'].map(node_map)
# 将 DataFrame 中的头尾节点 ID 替换为连续索引
# 这是图神经网络训练的必要预处理（GNN 要求节点索引从 0 开始连续）


# 3. 保存
os.makedirs('rec/algo/cache', exist_ok=True)    # 创建缓存目录
df.to_csv('rec/algo/cache/kg_triplet.csv', index=False)# 保存三元组为 CSV：head_id, tail_id, rel，index=False: 不保存行号
pickle.dump(node_map, open('rec/algo/cache/node_map.pkl', 'wb'))
# 用 pickle 序列化 node_map 字典
# 用途：后续将模型输出的索引映射回 Neo4j 节点，或反向查询
# 'wb': 二进制写入模式

print('导出完成：', len(nodes), '节点', len(df), '边')