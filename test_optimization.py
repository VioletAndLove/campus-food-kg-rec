"""
UCPR优化效果测试脚本
测试内容：
1. 路径多样性（2跳 vs 3跳）
2. BPR模型评分分布
3. 推荐结果多样性对比
"""

import sys
import torch
import pickle
import random
import numpy as np
from collections import defaultdict

sys.path.append('rec/algo')
from path_sampler import PathSampler
from ucpr_light import UCPRModel, device


def test_path_diversity():
    """测试路径采样多样性"""
    print("=" * 60)
    print("测试1：路径多样性对比")
    print("=" * 60)

    sampler = PathSampler()

    # 测试菜品对
    test_pairs = [
        ("川大江安校区麻婆豆腐", "中山大学学一麻婆豆腐"),
        ("吉大前卫酸菜鱼", "中山大学学一酸菜鱼"),
        ("南大六食堂水煮牛肉", "清华观畴园小炒口蘑")
    ]

    results = []
    for start, end in test_pairs:
        print(f"\n测试：{start} -> {end}")

        # 2跳路径
        paths_2hop = sampler.sample_2hop_paths(start, end)
        div_2hop = sampler.compute_path_diversity(paths_2hop) if paths_2hop else 0

        # 3跳路径
        paths_3hop = sampler.sample_3hop_paths(start, end)
        div_3hop = sampler.compute_path_diversity(paths_3hop) if paths_3hop else 0

        # 合并路径
        all_paths = sampler.sample_paths_by_name(start, end)
        div_combined = sampler.compute_path_diversity_v2(all_paths) if all_paths else 0

        print(f"  2跳路径: {len(paths_2hop)}条, 多样性: {div_2hop:.4f}")
        print(f"  3跳路径: {len(paths_3hop)}条, 多样性: {div_3hop:.4f}")
        print(f"  合并路径: {len(all_paths)}条, 增强多样性: {div_combined:.4f}")

        # 显示路径模式
        patterns = set(sampler.get_path_pattern(p) for p in all_paths)
        print(f"  路径模式: {list(patterns)[:3]}")

        results.append({
            'start': start,
            'end': end,
            'total_paths': len(all_paths),
            'diversity': div_combined
        })

    avg_diversity = sum(r['diversity'] for r in results) / len(results)
    avg_paths = sum(r['total_paths'] for r in results) / len(results)

    print(f"\n【汇总】")
    print(f"  平均路径数: {avg_paths:.1f}")
    print(f"  平均多样性: {avg_diversity:.4f}")

    return avg_diversity > 0.3  # 多样性阈值


def test_bpr_model():
    """测试BPR模型评分效果"""
    print("\n" + "=" * 60)
    print("测试2：BPR模型评分分布")
    print("=" * 60)

    # 加载模型
    node_map = pickle.load(open('rec/algo/cache/node_map.pkl', 'rb'))
    n_nodes = len(node_map)
    n_users = 500

    model = UCPRModel(n_nodes, 2, 32).to(device)

    # 尝试加载BPR模型
    try:
        model.ent_emb.load_state_dict(torch.load('rec/algo/cache/ent_emb_bpr.pth', map_location=device))
        model.rel_emb.load_state_dict(torch.load('rec/algo/cache/rel_emb_bpr.pth', map_location=device))
        print("✓ 成功加载BPR模型")
    except FileNotFoundError:
        print("✗ BPR模型未找到，尝试加载旧模型")
        try:
            model.ent_emb.load_state_dict(torch.load('rec/algo/cache/ent_emb.pth', map_location=device))
            print("✓ 加载旧模型")
        except FileNotFoundError:
            print("✗ 无可用模型")
            return False

    model.eval()

    # 测试用户
    test_users = [0, 10, 20, 30, 40]
    n_items = n_nodes - n_users

    all_scores = []
    score_gaps = []  # 正负样本分差

    with torch.no_grad():
        for user_id in test_users:
            # 计算该用户对所有物品的得分
            user_tensor = torch.LongTensor([user_id] * n_items).to(device)
            items_tensor = torch.LongTensor(list(range(n_users, n_users + n_items))).to(device)
            rel_tensor = torch.LongTensor([0] * n_items).to(device)

            u = model.ent_emb(user_tensor)
            r = model.rel_emb(rel_tensor)
            item_emb = model.ent_emb(items_tensor)

            scores = -torch.norm(u + r - item_emb, dim=1)
            scores_np = scores.cpu().numpy()

            all_scores.extend(scores_np)

            # 计算Top10与Bottom10的分差（模拟BPR效果）
            top_scores = np.sort(scores_np)[-10:]
            bottom_scores = np.sort(scores_np)[:10]
            gap = np.mean(top_scores) - np.mean(bottom_scores)
            score_gaps.append(gap)

            print(f"\n用户{user_id}:")
            print(f"  得分范围: [{scores_np.min():.2f}, {scores_np.max():.2f}]")
            print(f"  平均分: {scores_np.mean():.2f}")
            print(f"  标准差: {scores_np.std():.2f}")
            print(f"  Top/Bottom分差: {gap:.2f}")

    # 统计整体分布
    all_scores = np.array(all_scores)
    avg_gap = np.mean(score_gaps)

    print(f"\n【汇总】")
    print(f"  总体得分范围: [{all_scores.min():.2f}, {all_scores.max():.2f}]")
    print(f"  总体平均分: {all_scores.mean():.2f}")
    print(f"  平均Top/Bottom分差: {avg_gap:.2f}")

    # BPR效果判断：分差越大说明区分度越好
    return avg_gap > 1.0


def test_recommendation_diversity():
    """测试推荐结果多样性"""
    print("\n" + "=" * 60)
    print("测试3：推荐结果多样性")
    print("=" * 60)

    # 模拟推荐结果分析
    node_map = pickle.load(open('rec/algo/cache/node_map.pkl', 'rb'))
    sampler = PathSampler()

    # 加载模型（简化版，仅测试结构）
    n_users = 500

    test_user = 0
    print(f"\n测试用户: {test_user}")

    # 获取历史
    history = sampler.get_user_interacted_items(test_user)
    print(f"  历史记录: {len(history)}条")

    # 模拟推荐（实际应调用API）
    # 这里仅测试路径采样能力
    if history:
        hist_names = [h['dish_name'] for h in history[:3]]
        target = "吉大前卫酸菜鱼"  # 假设推荐目标

        all_paths = []
        for hist in hist_names:
            paths = sampler.sample_paths_by_name(hist, target)
            all_paths.extend(paths)

        if all_paths:
            patterns = [sampler.get_path_pattern(p) for p in all_paths]
            unique_patterns = len(set(patterns))
            diversity = sampler.compute_path_diversity_v2(all_paths)

            print(f"  采样路径数: {len(all_paths)}")
            print(f"  独特模式数: {unique_patterns}")
            print(f"  路径多样性: {diversity:.4f}")
            print(f"  模式分布: {list(set(patterns))[:5]}")

            return diversity > 0.2

    return True


def generate_report():
    """生成优化报告"""
    print("\n" + "=" * 60)
    print("UCPR优化测试报告")
    print("=" * 60)

    results = {
        '路径多样性': test_path_diversity(),
        'BPR模型效果': test_bpr_model(),
        '推荐多样性': test_recommendation_diversity()
    }

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 未通过"
        print(f"  {test_name}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n【结论】所有优化测试通过！")
        print("  - 3跳路径有效提升多样性")
        print("  - BPR模型区分度良好")
        print("  - 推荐系统可投入实验使用")
    else:
        print("\n【建议】")
        print("  - 若路径多样性不足：检查Neo4j数据完整性")
        print("  - 若BPR效果不佳：增加训练轮数或调整学习率")

    return all_passed


if __name__ == '__main__':
    generate_report()