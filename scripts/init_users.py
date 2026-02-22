# =============================================================================
# 功能：批量注册测试用户并生成模拟交互数据
# 归属：week11-12 用户实验准备
# 下游：Neo4j 中的 User 节点和 INTERACTED 关系
# =============================================================================

import requests
import random
import json

BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api/v1"

# 测试用户配置
NUM_USERS = 30  # 用户数量
INTERACTIONS_PER_USER = 15  # 每个用户的交互菜品数（模拟历史记录）

# 从 menu.json 加载菜品列表
import json

with open('data/menu.json', 'r', encoding='utf-8') as f:
    dishes = json.load(f)
    dish_names = [d['dish'] for d in dishes]

print(f"加载了 {len(dish_names)} 道菜品")


def register_user(username, password):
    """注册用户"""
    try:
        r = requests.post(
            f"{API_URL}/auth/register",
            json={"username": username, "password": password},
            timeout=5
        )
        if r.status_code == 200:
            return r.json()
        else:
            print(f"注册失败 {username}: {r.json().get('message', 'unknown error')}")
            return None
    except Exception as e:
        print(f"请求异常 {username}: {e}")
        return None


def create_interactions(user_id, token, num_interactions=15):
    """为用户生成模拟交互记录（直接写入 Neo4j）"""
    from py2neo import Graph

    graph = Graph("bolt://localhost:7687", auth=("neo4j", "wwj@51816888"))

    # 随机选择菜品
    selected_dishes = random.sample(dish_names, min(num_interactions, len(dish_names)))

    for dish_name in selected_dishes:
        # 随机评分 1-5
        rating = random.randint(1, 5)

        # 创建 INTERACTED 关系
        query = """
        MATCH (u:User {user_id: $user_id})
        MATCH (d:Dish {name: $dish_name})
        MERGE (u)-[r:INTERACTED]->(d)
        ON CREATE SET r.rating = $rating, r.timestamp = datetime()
        ON MATCH SET r.rating = $rating, r.timestamp = datetime()
        """

        try:
            graph.run(query, user_id=user_id, dish_name=dish_name, rating=rating)
        except Exception as e:
            print(f"  创建交互失败 {dish_name}: {e}")

    return len(selected_dishes)


def main():
    print(f"开始创建 {NUM_USERS} 个测试用户...")

    created_users = []

    for i in range(NUM_USERS):
        username = f"test_user_{i:03d}"  # test_user_000, test_user_001...
        password = "123456"

        print(f"\n[{i + 1}/{NUM_USERS}] 创建用户: {username}")

        # 注册
        user_info = register_user(username, password)
        if not user_info:
            continue

        user_id = user_info['user_id']
        token = user_info['access_token']

        print(f"  注册成功，user_id={user_id}")

        # 生成交互记录
        num_interactions = create_interactions(user_id, token, INTERACTIONS_PER_USER)
        print(f"  生成 {num_interactions} 条交互记录")

        created_users.append({
            'user_id': user_id,
            'username': username,
            'password': password,
            'interactions': num_interactions
        })

    # 保存用户信息（用于后续测试）
    with open('data/test_users.json', 'w', encoding='utf-8') as f:
        json.dump(created_users, f, ensure_ascii=False, indent=2)

    print(f"\n完成！创建了 {len(created_users)} 个用户")
    print(f"用户信息已保存到 data/test_users.json")


if __name__ == '__main__':
    main()