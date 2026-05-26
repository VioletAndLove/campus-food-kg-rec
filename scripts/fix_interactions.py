# =============================================================================
# 功能：修复用户交互记录数量，确保每人恰好15条
# =============================================================================

import json
import random
from py2neo import Graph

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "wwj@51816888")


def main():
    graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
    random.seed(42)

    with open("data/menu.json", "r", encoding="utf-8") as f:
        dishes = [d["dish"] for d in json.load(f)]

    # Find users with != 15 interactions
    result = graph.run("""
        MATCH (u:User)
        OPTIONAL MATCH (u)-[r:INTERACTED]->()
        WITH u.user_id as uid, count(r) as cnt
        WHERE cnt <> 15
        RETURN uid, cnt
        ORDER BY cnt
    """).data()

    print(f"Found {len(result)} users with != 15 interactions")

    for row in result:
        uid = row["uid"]
        cnt = row["cnt"]

        if cnt < 15:
            # Need to add interactions
            existing = graph.run("""
                MATCH (u:User {user_id: $uid})-[r:INTERACTED]->(d)
                RETURN d.name as name
            """, uid=uid).data()
            existing_names = {r["name"] for r in existing}
            available = [d for d in dishes if d not in existing_names]
            needed = 15 - cnt
            selected = random.sample(available, needed)

            interactions = []
            for dish_name in selected:
                interactions.append({
                    "user_id": uid,
                    "dish_name": dish_name,
                    "rating": random.randint(1, 5),
                })

            graph.run("""
                UNWIND $interactions as rel
                MATCH (u:User {user_id: rel.user_id})
                MATCH (d:Dish {name: rel.dish_name})
                CREATE (u)-[r:INTERACTED]->(d)
                SET r.rating = rel.rating, r.timestamp = datetime()
            """, interactions=interactions)
            print(f"  User {uid}: added {needed} interactions (was {cnt})")

        elif cnt > 15:
            # Need to remove extra interactions
            to_remove = cnt - 15
            graph.run("""
                MATCH (u:User {user_id: $uid})-[r:INTERACTED]->()
                WITH r LIMIT $limit
                DELETE r
            """, uid=uid, limit=to_remove)
            print(f"  User {uid}: removed {to_remove} interactions (was {cnt})")

    # Final verification
    result = graph.run("""
        MATCH (u:User)
        OPTIONAL MATCH (u)-[r:INTERACTED]->()
        WITH u.user_id as uid, count(r) as cnt
        WHERE cnt <> 15
        RETURN uid, cnt
        ORDER BY cnt
    """).data()

    if result:
        print("Still have users with != 15 interactions:")
        for r in result:
            print(f"  user_id={r['uid']}, count={r['cnt']}")
    else:
        print("All users now have exactly 15 interactions!")


if __name__ == "__main__":
    main()
