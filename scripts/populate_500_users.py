# =============================================================================
# 功能：批量扩充用户至500人，每人15条交互记录（含评论内容）
# 归属：数据填充脚本
# 上游：data/menu.json（菜品数据源）
# 下游：Neo4j User节点、INTERACTED关系、RATED关系、data/test_users.json
# =============================================================================

import json
import hashlib
import random
from datetime import datetime, timedelta
from py2neo import Graph

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "wwj@51816888")

TARGET_USERS = 500
INTERACTIONS_PER_USER = 15
BATCH_SIZE_USERS = 100
BATCH_SIZE_INTERACTIONS = 500
PASSWORD = "123456"

# 评论模板库（按星级分类）
COMMENT_TEMPLATES = {
    5: [
        "太好吃了！强烈推荐给大家！", "味道非常棒，分量也很足，下次还会再来！",
        "这是我吃过最好吃的菜之一！", "超级满意，完全符合我的口味！", "绝了，五星好评！",
        "口感特别好，厨师手艺真棒！", "强烈推荐，绝对不会失望！", "满分体验，下次带朋友一起来！",
        "色香味俱全，太赞了！", "无可挑剔，必须给五星！", "非常惊喜，超出预期的好吃！",
        "每吃一口都是享受！", "性价比超高，味道一流！", "真的太好吃了，每天都要来！",
        "正宗的味道，满满的幸福感！", "推荐给大家，一定不会后悔！", "菜品新鲜，口味极佳！",
        "最爱这家了，五星好评！", "吃得很开心，心情都变好了！", "无可挑剔的美食体验！"
    ],
    4: [
        "味道不错，挺满意的。", "整体来说还是很好吃的，推荐！", "挺喜欢的，稍微有点咸。",
        "不错的体验，大部分都很满意。", "味道很好，就是排队时间有点长。", "性价比高，值得一试！",
        "口味不错，分量也还可以。", "挺好吃的一道菜，会回购。", "味道挺正的，点个赞！",
        "整体不错，就是价格稍微贵了点。", "食材新鲜，味道也可以。", "比较满意，适合我的口味。",
        "好吃，但还有提升空间。", "不错的菜品，经常来。", "味道可以，环境也不错。",
        "总体满意，希望保持水准。", "挺喜欢这种口味的。", "值得尝试，推荐给大家。",
        "味道很好，服务态度也不错。", "基本满意，会再来光顾。"
    ],
    3: [
        "一般般吧，没什么特别。", "味道还可以，就是不够惊艳。", "普通水平，不算好吃也不算难吃。",
        "中规中矩，谈不上好也谈不上坏。", "还行，但不符合我的期待。", "分量一般，味道还可以。",
        "谈不上喜欢也谈不上讨厌。", "没有想象中好吃。", "还行吧，偶尔吃一次可以。",
        "一般般，吃完就忘了味道。", "普通口感，没什么亮点。", "味道还可以再改进一下。",
        "就正常水平吧。", "还行，但不会再特意来。", "勉强可以接受。",
        "味道有点平淡。", "中规中矩的体验。", "一般，没有特别的印象。",
        "普通的菜，没有惊喜。", "还行，看个人口味吧。"
    ],
    2: [
        "不太好吃，有点失望。", "味道一般，不太符合我的口味。", "不太推荐，吃着不太舒服。",
        "味道有点怪，不太习惯。", "分量太少了，性价比不高。", "做得不够入味，一般。",
        "有点油腻，不太喜欢。", "不太满意，和预期差很多。", "口感不太好，有点柴。",
        "味道偏淡/偏咸，不太合适。", "不太新鲜的感觉。", "吃过更好的，这个一般。",
        "不太合胃口。", "做得不够细致。", "有点踩雷了。",
        "不太推荐这个菜。", "有点难以下咽。", "吃了一半就不想吃了。",
        "希望改进一下做法。", "不太适合我。"
    ],
    1: [
        "太难吃了，完全无法接受！", "非常失望，浪费钱！", "这是我吃过最难吃的菜！",
        "简直不能吃，味道太奇怪了！", "强烈不推荐，大家避雷！", "太难以下咽了，简直糟蹋食材！",
        "完全不符合预期，太差了！", "吃了一口就不想吃了！", "非常糟糕的体验！",
        "味道很怪，像是做坏了！", "太让人失望了！", "绝对不能点这道菜！",
        "恶心，很难吃！", "完全不能接受的味道！", "太咸/太淡/太辣，无法入口！",
        "糟蹋了这么好的食材！", "非常不满意！", "劝大家别尝试！",
        "一星都不想给！", "极其糟糕的体验！"
    ]
}


def load_dishes():
    with open("data/menu.json", "r", encoding="utf-8") as f:
        dishes = json.load(f)
    return [d["dish"] for d in dishes]


def md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def get_current_stats(graph):
    result = graph.run("MATCH (u:User) RETURN count(u) as cnt, coalesce(max(u.user_id), -1) as max_id").data()
    return result[0]["cnt"], result[0]["max_id"]


def create_users_batch(graph, users_batch):
    """使用UNWIND批量创建用户"""
    query = """
    UNWIND $users as user
    CREATE (u:User {
        user_id: user.user_id,
        username: user.username,
        password_hash: user.password_hash,
        created_at: datetime()
    })
    """
    graph.run(query, users=users_batch)


def create_interactions_batch(graph, interactions_batch):
    """使用UNWIND批量创建INTERACTED关系（用于历史记录和推荐）"""
    query = """
    UNWIND $interactions as rel
    MATCH (u:User {user_id: rel.user_id})
    MATCH (d:Dish {name: rel.dish_name})
    CREATE (u)-[r:INTERACTED]->(d)
    SET r.rating = rel.rating, r.timestamp = rel.ts
    """
    graph.run(query, interactions=interactions_batch)


def create_ratings_batch(graph, ratings_batch):
    """使用UNWIND批量创建RATED关系（用于评论区展示）"""
    query = """
    UNWIND $ratings as rel
    MATCH (u:User {user_id: rel.user_id})
    MATCH (d:Dish {name: rel.dish_name})
    CREATE (u)-[r:RATED]->(d)
    SET r.rating = rel.rating, r.content = rel.content,
        r.created_at = rel.ts, r.is_anonymous = rel.is_anonymous,
        r.likes = 0
    """
    graph.run(query, ratings=ratings_batch)


def generate_comment(rating):
    """根据评分生成评论内容"""
    templates = COMMENT_TEMPLATES.get(rating, COMMENT_TEMPLATES[3])
    return random.choice(templates)


def main():
    graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
    dish_names = load_dishes()
    current_count, max_id = get_current_stats(graph)

    print(f"当前用户数量: {current_count}, 最大 user_id: {max_id}")

    # 检查 RATED 关系数量
    rated_count = graph.run("MATCH ()-[r:RATED]->() RETURN count(r) as cnt").data()[0]["cnt"]
    print(f"当前 RATED 关系数量: {rated_count}")

    # 如果已有500用户但缺少 RATED 关系，只为已有用户补充评论
    if current_count >= TARGET_USERS and rated_count < current_count * INTERACTIONS_PER_USER * 0.5:
        print(f"用户数量已达 {current_count}，但 RATED 关系不足，开始补充评论数据...")
        fill_ratings_only(graph, dish_names, current_count)
        return
    elif current_count >= TARGET_USERS:
        print(f"用户数量已达 {current_count}，且 RATED 关系充足，无需补充")
        return

    need_to_create = TARGET_USERS - current_count
    print(f"需要创建 {need_to_create} 个新用户，目标总数 {TARGET_USERS}")

    start_id = max_id + 1
    end_id = TARGET_USERS - 1  # user_id 0~499

    all_new_users = []
    all_interactions = []
    all_ratings = []

    random.seed(42)

    for user_id in range(start_id, end_id + 1):
        username = f"test_user_{user_id:03d}"
        user = {
            "user_id": user_id,
            "username": username,
            "password_hash": md5_hash(PASSWORD),
        }
        all_new_users.append(user)

        # 为该用户生成15条交互记录
        selected_dishes = random.sample(dish_names, INTERACTIONS_PER_USER)
        for dish_name in selected_dishes:
            # 生成过去90天内的随机时间
            days_ago = random.randint(0, 90)
            hours_ago = random.randint(0, 23)
            ts = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
            ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S")

            rating = random.randint(1, 5)
            is_anon = random.random() < 0.15  # 15%概率匿名

            # INTERACTED 关系（用于历史记录和推荐）
            all_interactions.append({
                "user_id": user_id,
                "dish_name": dish_name,
                "rating": rating,
                "ts": ts_str,
            })

            # RATED 关系（用于评论区展示）
            all_ratings.append({
                "user_id": user_id,
                "dish_name": dish_name,
                "rating": rating,
                "content": generate_comment(rating),
                "ts": ts_str,
                "is_anonymous": is_anon,
            })

    # 批量写入用户
    print(f"\n开始批量写入 {len(all_new_users)} 个用户...")
    for i in range(0, len(all_new_users), BATCH_SIZE_USERS):
        batch = all_new_users[i:i + BATCH_SIZE_USERS]
        create_users_batch(graph, batch)
        print(f"  已写入用户 {i + len(batch)} / {len(all_new_users)}")

    # 批量写入 INTERACTED 关系
    print(f"\n开始批量写入 {len(all_interactions)} 条 INTERACTED 关系...")
    for i in range(0, len(all_interactions), BATCH_SIZE_INTERACTIONS):
        batch = all_interactions[i:i + BATCH_SIZE_INTERACTIONS]
        create_interactions_batch(graph, batch)
        print(f"  已写入 INTERACTED {i + len(batch)} / {len(all_interactions)}")

    # 批量写入 RATED 关系
    print(f"\n开始批量写入 {len(all_ratings)} 条 RATED 关系（含评论）...")
    for i in range(0, len(all_ratings), BATCH_SIZE_INTERACTIONS):
        batch = all_ratings[i:i + BATCH_SIZE_INTERACTIONS]
        create_ratings_batch(graph, batch)
        print(f"  已写入 RATED {i + len(batch)} / {len(all_ratings)}")

    # 更新 test_users.json
    print("\n更新 data/test_users.json ...")
    try:
        with open("data/test_users.json", "r", encoding="utf-8") as f:
            existing_users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_users = []

    # 构造完整用户列表（保留已有，追加新用户）
    existing_ids = {u["user_id"] for u in existing_users}
    for user in all_new_users:
        if user["user_id"] not in existing_ids:
            existing_users.append({
                "user_id": user["user_id"],
                "username": user["username"],
                "password": PASSWORD,
                "interactions": INTERACTIONS_PER_USER,
            })

    with open("data/test_users.json", "w", encoding="utf-8") as f:
        json.dump(existing_users, f, ensure_ascii=False, indent=2)

    # 最终验证
    final_count, final_max_id = get_current_stats(graph)
    final_interactions = graph.run(
        "MATCH ()-[r:INTERACTED]->() RETURN count(r) as cnt"
    ).data()[0]["cnt"]
    final_ratings = graph.run(
        "MATCH ()-[r:RATED]->() RETURN count(r) as cnt"
    ).data()[0]["cnt"]

    print(f"\n✅ 完成！")
    print(f"   用户总数: {final_count} / {TARGET_USERS}")
    print(f"   最大 user_id: {final_max_id}")
    print(f"   INTERACTED 关系总数: {final_interactions}")
    print(f"   RATED 关系总数（含评论）: {final_ratings}")
    print(f"   数据已保存到 data/test_users.json")


def fill_ratings_only(graph, dish_names, user_count):
    """为已有用户补充 RATED 关系（含评论内容）"""
    # 获取所有已有的 User 和 INTERACTED 关系
    query = """
    MATCH (u:User)-[r:INTERACTED]->(d:Dish)
    RETURN u.user_id as user_id, d.name as dish_name, r.rating as rating, r.timestamp as ts
    """
    existing_interactions = graph.run(query).data()

    # 检查哪些已有 INTERACTED 但缺少 RATED
    check_query = """
    MATCH (u:User)-[r:INTERACTED]->(d:Dish)
    WHERE NOT (u)-[:RATED]->(d)
    RETURN u.user_id as user_id, d.name as dish_name, r.rating as rating, r.timestamp as ts
    """
    missing = graph.run(check_query).data()

    if not missing:
        print("所有交互记录都已包含评论数据，无需补充")
        return

    print(f"发现 {len(missing)} 条缺少评论的交互记录，开始补充...")

    all_ratings = []
    random.seed(42)

    for row in missing:
        ts = row['ts']
        if hasattr(ts, 'isoformat'):
            ts_str = ts.isoformat()
        else:
            ts_str = str(ts)

        rating = int(row['rating']) if row['rating'] else random.randint(1, 5)
        is_anon = random.random() < 0.15

        all_ratings.append({
            "user_id": int(row['user_id']),
            "dish_name": row['dish_name'],
            "rating": rating,
            "content": generate_comment(rating),
            "ts": ts_str,
            "is_anonymous": is_anon,
        })

    # 批量写入 RATED 关系
    BATCH = 500
    print(f"\n开始批量写入 {len(all_ratings)} 条 RATED 关系（含评论）...")
    for i in range(0, len(all_ratings), BATCH):
        batch = all_ratings[i:i + BATCH]
        create_ratings_batch(graph, batch)
        print(f"  已写入 RATED {i + len(batch)} / {len(all_ratings)}")

    final_ratings = graph.run("MATCH ()-[r:RATED]->() RETURN count(r) as cnt").data()[0]["cnt"]
    print(f"\n✅ 评论数据补充完成！当前 RATED 关系总数: {final_ratings}")


if __name__ == "__main__":
    main()
