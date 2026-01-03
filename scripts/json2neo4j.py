from py2neo import Graph, Node, Relationship
import json, sys

graph = Graph("bolt://localhost:7687", auth=("neo4j", "wwj@51816888"))
menu = json.load(open('data/menu.json', encoding='utf-8'))

graph.run("MATCH (n) DETACH DELETE n")  # 清空旧数据（调试用）

for m in menu:
    dish = Node("Dish", name=m['dish'], price=m['price'], file=m['file'], note=m['note'])
    graph.create(dish)
    for t in m['tags']:
        tag = Node("Tag", name=t)
        graph.merge(tag, "Tag", "name")
        graph.create(Relationship(dish, "HAS_TAG", tag))
    for i in m['ingredients']:
        ing = Node("Ingredient", name=i)
        graph.merge(ing, "Ingredient", "name")
        graph.create(Relationship(dish, "CONTAINS", ing))

print("✅ KG 构建完成，共导入", len(menu), "道菜品")