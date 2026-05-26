# =============================================================================
# 功能：离线分析高频套餐组合，为推荐策略调参提供数据支撑
# 归属：weekX 套餐推荐模块（可选增强）
# 上游：Neo4j 中的 INTERACTED 关系
# 下游：data/combo_stats.json（统计报告）
# =============================================================================

from py2neo import Graph
from collections import Counter
import json

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "wwj@51816888")


def analyze_combo_patterns(graph, min_cooccur=5):
    """
    分析用户交互数据中的高频菜品共现模式
    """
    print("正在分析高频共现组合...")

    # 1. 统计每对用户同时交互的菜品对
    query = """
    MATCH (u:User)-[:INTERACTED]->(d1:Dish)
    MATCH (u)-[:INTERACTED]->(d2:Dish)
    WHERE id(d1) < id(d2)
    RETURN d1.name as dish_a, d2.name as dish_b, count(u) as freq
    ORDER BY freq DESC
    LIMIT 100
    """
    pairs = graph.run(query).data()

    top_pairs = []
    for p in pairs:
        if p['freq'] >= min_cooccur:
            top_pairs.append({
                "dishes": [p['dish_a'], p['dish_b']],
                "co_occurrence": int(p['freq'])
            })

    # 2. 统计最常出现的"第三道菜"（三元组）
    print("正在分析高频三元组...")
    triple_query = """
    MATCH (u:User)-[:INTERACTED]->(d1:Dish)
    MATCH (u)-[:INTERACTED]->(d2:Dish)
    MATCH (u)-[:INTERACTED]->(d3:Dish)
    WHERE id(d1) < id(d2) AND id(d2) < id(d3)
    RETURN d1.name as a, d2.name as b, d3.name as c, count(u) as freq
    ORDER BY freq DESC
    LIMIT 50
    """
    triples = graph.run(triple_query).data()

    top_triples = []
    for t in triples:
        if t['freq'] >= min_cooccur:
            top_triples.append({
                "dishes": [t['a'], t['b'], t['c']],
                "co_occurrence": int(t['freq'])
            })

    # 3. 统计各标签的共现偏好
    print("正在分析标签共现偏好...")
    tag_query = """
    MATCH (d1:Dish)-[:HAS_TAG]->(t1:Tag)
    MATCH (d2:Dish)-[:HAS_TAG]->(t2:Tag)
    MATCH (u:User)-[:INTERACTED]->(d1)
    MATCH (u)-[:INTERACTED]->(d2)
    WHERE d1 <> d2 AND t1.name < t2.name
    RETURN t1.name as tag_a, t2.name as tag_b, count(DISTINCT u) as freq
    ORDER BY freq DESC
    LIMIT 50
    """
    tag_pairs = graph.run(tag_query).data()

    top_tag_pairs = []
    for tp in tag_pairs:
        if tp['freq'] >= min_cooccur:
            top_tag_pairs.append({
                "tags": [tp['tag_a'], tp['tag_b']],
                "co_occurrence": int(tp['freq'])
            })

    # 4. 统计平均套餐价格分布
    print("正在分析用户消费分布...")
    price_query = """
    MATCH (u:User)-[:INTERACTED]->(d:Dish)
    WITH u, sum(d.price) as total, count(d) as cnt
    WHERE cnt >= 2
    RETURN avg(total) as avg_total, percentileDisc(total, 0.5) as median_total,
           avg(cnt) as avg_dish_count
    """
    price_stats = graph.run(price_query).data()[0]

    report = {
        "summary": {
            "total_users_analyzed": graph.run("MATCH (u:User) RETURN count(u) as cnt").data()[0]['cnt'],
            "total_interactions": graph.run("MATCH ()-[r:INTERACTED]->() RETURN count(r) as cnt").data()[0]['cnt'],
            "avg_combo_price": round(float(price_stats['avg_total'] or 0), 2),
            "median_combo_price": round(float(price_stats['median_total'] or 0), 2),
            "avg_dishes_per_user": round(float(price_stats['avg_dish_count'] or 0), 2),
        },
        "top_pairs": top_pairs[:20],
        "top_triples": top_triples[:10],
        "top_tag_pairs": top_tag_pairs[:20],
    }

    return report


def main():
    graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
    report = analyze_combo_patterns(graph, min_cooccur=3)

    output_file = "data/combo_stats.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n分析完成！报告已保存到 {output_file}")
    print(f"分析用户数: {report['summary']['total_users_analyzed']}")
    print(f"平均组合消费: ¥{report['summary']['avg_combo_price']}")
    print(f"高频菜品对: {len(report['top_pairs'])} 组")
    print(f"高频三元组: {len(report['top_triples'])} 组")


if __name__ == "__main__":
    main()
