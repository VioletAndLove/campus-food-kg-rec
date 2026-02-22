"""
功能：准备 A/B 测试实验
- 将 30 个测试用户随机分为 A/B 两组
- A 组：显示解释路径（实验组）
- B 组：不显示解释路径（对照组）
- 生成实验配置文件供前端读取
"""

import json
import random
import os

random.seed(42)  # 可复现

# 加载测试用户
with open('data/test_users.json', 'r', encoding='utf-8') as f:
    users = json.load(f)

# 随机分组
user_ids = [u['user_id'] for u in users]
random.shuffle(user_ids)
mid = len(user_ids) // 2

group_a = user_ids[:mid]   # 有解释
group_b = user_ids[mid:]   # 无解释

experiment_config = {
    "experiment_id": "exp_2024_001",
    "description": "可解释推荐 vs 无解释推荐 对比实验",
    "groups": {
        "A": {
            "name": "实验组（有解释）",
            "user_ids": group_a,
            "show_explanation": True,
            "sample_size": len(group_a)
        },
        "B": {
            "name": "对照组（无解释）",
            "user_ids": group_b,
            "show_explanation": False,
            "sample_size": len(group_b)
        }
    },
    "metrics": ["click_rate", "satisfaction", "diversity_score"],
    "start_date": "2024-03-01",
    "end_date": "2024-03-15"
}

os.makedirs('data/experiment', exist_ok=True)
with open('data/experiment/ab_test_config.json', 'w', encoding='utf-8') as f:
    json.dump(experiment_config, f, ensure_ascii=False, indent=2)

print(f"A/B 测试配置已生成")
print(f"实验组（A）: {len(group_a)} 人，显示解释路径")
print(f"对照组（B）: {len(group_b)} 人，隐藏解释路径")
print(f"配置文件: data/experiment/ab_test_config.json")

# 同时生成用户分组查询表
user_group_map = {uid: 'A' for uid in group_a}
user_group_map.update({uid: 'B' for uid in group_b})
with open('data/experiment/user_group_map.json', 'w', encoding='utf-8') as f:
    json.dump(user_group_map, f, ensure_ascii=False, indent=2)