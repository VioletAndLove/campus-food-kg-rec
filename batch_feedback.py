"""
批量提交A/B测试反馈（模拟真实用户评分）
"""
import requests
import json
import random
import time

BASE_URL = "http://localhost:5000/api/v1"

def login(username, password="123456"):
    """登录获取token"""
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "username": username,
            "password": password
        }, timeout=5)
        if r.status_code == 200:
            return r.json()['access_token']
    except Exception as e:
        print(f"登录失败 {username}: {e}")
    return None

def get_recommendations(token, user_id, topk=5):
    """获取推荐列表"""
    try:
        r = requests.post(f"{BASE_URL}/rec/",
            json={"user_id": user_id, "topk": topk},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if r.status_code == 200:
            return r.json().get('recommendations', [])
    except Exception as e:
        print(f"获取推荐失败: {e}")
    return []

def submit_feedback(token, dish_id, rating, comment=""):
    """提交反馈"""
    try:
        r = requests.post(f"{BASE_URL}/feedback/",
            json={
                "dish_id": dish_id,
                "rating": rating,
                "clicked": True,
                "comment": comment
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        return r.status_code == 200
    except Exception as e:
        print(f"提交反馈失败: {e}")
    return False

def simulate_user(username, user_id):
    """模拟单个用户行为"""
    print(f"\n模拟用户: {username}")

    # 登录
    token = login(username)
    if not token:
        return False

    # 获取推荐
    recs = get_recommendations(token, user_id, topk=3)
    if not recs:
        print("  无推荐结果")
        return False

    print(f"  获取 {len(recs)} 条推荐")

    # 随机选择1-2个菜品评分
    selected = random.sample(recs, min(random.randint(1, 2), len(recs)))

    for dish in selected:
        # 随机评分（3-5星为主，模拟正常用户）
        rating = random.choices([3, 4, 5], weights=[0.2, 0.5, 0.3])[0]

        # 根据评分生成评论
        comments = {
            5: ["很好吃", "推荐", "不错", "满意"],
            4: ["还可以", "一般", "还行", ""],
            3: ["一般", "不太满意", "普通", ""]
        }
        comment = random.choice(comments.get(rating, [""]))

        # 提交反馈
        success = submit_feedback(token, dish['dish_id'], rating, comment)
        if success:
            print(f"  ✓ {dish['dish_name']}: {rating}星 - {comment}")
        else:
            print(f"  ✗ {dish['dish_name']}: 提交失败")

        time.sleep(0.5)  # 避免请求过快

    return True

def main():
    # 加载用户分组
    with open('data/experiment/user_group_map.json') as f:
        groups = json.load(f)

    with open('data/test_users.json') as f:
        users = json.load(f)

    # 按分组筛选用户
    group_a = [u for u in users if groups.get(str(u['user_id'])) == 'A']
    group_b = [u for u in users if groups.get(str(u['user_id'])) == 'B']

    print(f"A组用户: {len(group_a)}个")
    print(f"B组用户: {len(group_b)}个")

    # 选择未测试或测试少的用户（前10个）
    test_a = group_a[:10]
    test_b = group_b[:10]

    print(f"\n计划测试: A组{len(test_a)}个 + B组{len(test_b)}个")
    print("=" * 50)

    # 执行测试
    success_count = 0
    for u in test_a + test_b:
        if simulate_user(u['username'], u['user_id']):
            success_count += 1
        time.sleep(1)  # 用户间隔

    print(f"\n{'=' * 50}")
    print(f"完成: {success_count}/{len(test_a) + len(test_b)} 个用户")
    print("请运行 analyze_experiment.py 查看结果")

if __name__ == '__main__':
    main()