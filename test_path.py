# =============================================================================
# 功能：测试路径采样器是否正常工作
# =============================================================================

import sys

sys.path.append('.')

from rec.algo.path_sampler import PathSampler

sampler = PathSampler()

# 测试 1：检查 Neo4j 连接
print("=" * 50)
print("测试 1：Neo4j 连接")
try:
    # 获取用户 1 的历史交互
    history = sampler.get_user_interacted_items(1)
    print(f"用户 1 的历史记录：{len(history)} 条")
    for h in history[:3]:
        print(f"  - {h['dish_name']} (评分: {h['rating']})")
except Exception as e:
    print(f"失败: {e}")

# 测试 2 修改：
print("\n" + "=" * 50)
print("测试 2：路径采样")

# 直接测试两个有共享标签的菜品
start_name = "川大江安校区麻婆豆腐"
end_name = "中山大学学一麻婆豆腐"  # 从 Neo4j 查询结果中确认的相似菜品

print(f"尝试采样 '{start_name}' 到 '{end_name}' 的路径...")

paths = sampler.sample_paths_by_name(start_name, end_name)
print(f"采样到 {len(paths)} 条路径")

for i, p in enumerate(paths):
    pattern = sampler.get_path_pattern(p)
    print(f"\n路径 {i+1}: {pattern}")
    print(f"  详情: {p}")

# 测试 3：路径多样性计算
print("\n" + "=" * 50)
print("测试 3：路径多样性")
if paths:
    diversity = sampler.compute_path_diversity(paths)
    print(f"路径多样性 (SID): {diversity:.4f}")
else:
    print("无路径，无法计算多样性")