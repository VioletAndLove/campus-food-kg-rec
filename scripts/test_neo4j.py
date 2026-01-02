from py2neo import Graph
g = Graph("bolt://localhost:7687", auth=("neo4j", "wwj@51816888"))
g.run("CREATE (n:TestNode {name:'hello-neo4j'})")
data = g.run("MATCH (n:TestNode) RETURN n.name as name").data()
print(data)