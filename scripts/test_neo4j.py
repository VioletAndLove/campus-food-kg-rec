# =============================================================================
# 功能：Neo4j 数据库连接测试脚本，验证环境配置正确性
# 归属：week1-2 技术验证阶段 / 日常调试工具
# 上游：无（独立运行）
# 下游：无（仅验证连接）
# =============================================================================

from py2neo import Graph
g = Graph("bolt://localhost:7687", auth=("neo4j", "wwj@51816888"))
g.run("CREATE (n:TestNode {name:'hello-neo4j'})")
data = g.run("MATCH (n:TestNode) RETURN n.name as name").data()
print(data)