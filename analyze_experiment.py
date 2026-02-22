"""
A/B 测试实验数据分析脚本
功能：统计A/B组满意度差异，生成实验报告
"""

import json
import os
from collections import defaultdict
import statistics


def load_feedback_data():
    """加载用户反馈数据"""
    log_file = 'data/experiment/feedback_log.jsonl'
    if not os.path.exists(log_file):
        print(f"反馈文件不存在: {log_file}")
        return []

    records = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def load_group_map():
    """加载用户分组信息"""
    group_file = 'data/experiment/user_group_map.json'
    if not os.path.exists(group_file):
        print(f"分组文件不存在: {group_file}")
        return {}

    with open(group_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_by_group(records, group_map):
    """按A/B组分析反馈数据"""
    group_stats = {
        'A': {'ratings': [], 'count': 0, 'comments': []},
        'B': {'ratings': [], 'count': 0, 'comments': []}
    }

    for record in records:
        user_id = str(record.get('user_id'))
        group = group_map.get(user_id, 'unknown')

        if group not in ['A', 'B']:
            continue

        rating = record.get('rating', 0)
        if rating > 0:
            group_stats[group]['ratings'].append(rating)
            group_stats[group]['count'] += 1

        comment = record.get('comment', '').strip()
        if comment:
            group_stats[group]['comments'].append(comment)

    return group_stats


def calculate_metrics(ratings):
    """计算统计指标"""
    if not ratings:
        return {'mean': 0, 'median': 0, 'std': 0, 'count': 0}

    return {
        'mean': round(statistics.mean(ratings), 2),
        'median': round(statistics.median(ratings), 2),
        'std': round(statistics.stdev(ratings), 2) if len(ratings) > 1 else 0,
        'count': len(ratings),
        'distribution': {
            '5星': ratings.count(5),
            '4星': ratings.count(4),
            '3星': ratings.count(3),
            '2星': ratings.count(2),
            '1星': ratings.count(1)
        }
    }


def print_report(stats):
    """打印实验报告"""
    print("=" * 60)
    print("A/B 测试实验报告")
    print("=" * 60)

    for group in ['A', 'B']:
        data = stats[group]
        metrics = calculate_metrics(data['ratings'])

        print(f"\n【{'实验组（A）' if group == 'A' else '对照组（B）'}】")
        print(f"  样本量: {metrics['count']} 条评价")
        print(f"  平均满意度: {metrics['mean']} 分")
        print(f"  中位数: {metrics['median']} 分")
        print(f"  标准差: {metrics['std']}")

        if metrics['count'] > 0:
            print(f"  评分分布:")
            for star, count in metrics['distribution'].items():
                bar = '█' * count
                print(f"    {star}: {bar} ({count})")

        if data['comments']:
            print(f"  用户评论（{len(data['comments'])}条）:")
            for i, comment in enumerate(data['comments'][:3], 1):
                print(f"    {i}. {comment[:50]}{'...' if len(comment) > 50 else ''}")

    # 组间对比
    a_ratings = stats['A']['ratings']
    b_ratings = stats['B']['ratings']

    if a_ratings and b_ratings:
        a_mean = statistics.mean(a_ratings)
        b_mean = statistics.mean(b_ratings)
        diff = a_mean - b_mean

        print(f"\n【组间对比】")
        print(f"  实验组(A) vs 对照组(B): {a_mean:.2f} vs {b_mean:.2f}")
        print(f"  差异: {diff:+.2f} 分")
        print(f"  提升幅度: {(diff / b_mean) * 100:+.1f}%" if b_mean > 0 else "  N/A")

        if diff > 0:
            print(f"  结论: 显示解释路径（A组）满意度更高")
        elif diff < 0:
            print(f"  结论: 隐藏解释路径（B组）满意度更高")
        else:
            print(f"  结论: 两组满意度无差异")

    print("\n" + "=" * 60)


def export_report(stats, filename='data/experiment/analysis_report.json'):
    """导出分析报告"""
    report = {
        'experiment_id': 'exp_2024_001',
        'groups': {}
    }

    for group in ['A', 'B']:
        metrics = calculate_metrics(stats[group]['ratings'])
        report['groups'][group] = {
            'name': '实验组（显示解释）' if group == 'A' else '对照组（隐藏解释）',
            'metrics': metrics,
            'sample_size': metrics['count']
        }

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n报告已导出: {filename}")


def main():
    print("正在分析 A/B 测试数据...\n")

    # 加载数据
    records = load_feedback_data()
    group_map = load_group_map()

    if not records:
        print("暂无反馈数据，请先进行用户测试")
        print("\n测试流程:")
        print("1. 登录 test_user_000 ~ test_user_029 账号")
        print("2. 点击推荐菜品进入详情页")
        print("3. 提交满意度评分")
        print("4. 再次运行本脚本")
        return

    print(f"加载到 {len(records)} 条反馈记录")
    print(f"分组信息: {len(group_map)} 个用户")

    # 分析
    stats = analyze_by_group(records, group_map)

    # 输出报告
    print_report(stats)

    # 导出JSON
    export_report(stats)

    print("\n分析完成！")


if __name__ == '__main__':
    main()