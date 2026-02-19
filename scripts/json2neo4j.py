# =============================================================================
# 功能：将 JSON 格式的菜品数据导入 Neo4j 图数据库，构建知识图谱
# 归属：week3-4 数据层任务（构图阶段）
# 上游：data/menu.json（excel2json.py 的输出）
# 下游：Neo4j 数据库（供 week5-6 推荐算法查询）
# =============================================================================




from py2neo import Graph, Node, Relationship
import json, sys
# Graph: Neo4j 数据库连接对象
# Node: 图谱节点（实体）
# Relationship: 图谱关系（边）


graph = Graph("bolt://localhost:7687", auth=("neo4j", "wwj@51816888"))  # 连接 Neo4j
menu = json.load(open('data/menu.json', encoding='utf-8'))      # 读取 excel2json.py 生成的 JSON 文件

graph.run("MATCH (n) DETACH DELETE n")  # 清空旧数据（调试用）

for m in menu:   # 遍历每道菜品
    dish = Node("Dish", name=m['dish'], price=m['price'], file=m['file'], note=m['note'])        # 创建 Dish 类型节点，包含名称、价格、照片、备注属性
    graph.create(dish)      # 立即创建节点（非幂等，若重复运行会创建重复节点，但前面已清空）
    for t in m['tags']:
        tag = Node("Tag", name=t)   # 创建 Tag 类型节点
        graph.merge(tag, "Tag", "name")   # 幂等创建：若 name 属性相同的 Tag 已存在则复用，否则新建
        graph.create(Relationship(dish, "HAS_TAG", tag))    # 创建 Dish-[HAS_TAG]->Tag 关系
    for i in m['ingredients']:
        ing = Node("Ingredient", name=i)   # 创建 Ingredient 类型节点
        graph.merge(ing, "Ingredient", "name")   # 幂等创建食材节点，相同食材复用
        graph.create(Relationship(dish, "CONTAINS", ing))

print("✅ KG 构建完成，共导入", len(menu), "道菜品")