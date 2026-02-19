from flask_restx import Namespace, Resource, fields
from py2neo import Graph
from flask import current_app
import torch
import pandas as pd
import os
import sys
import json
import hashlib
import pickle

# 路径处理
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from algo.ucpr_light import ent_emb, n_users, EMB, device

rec_bp = Namespace("rec", description="菜品推荐服务")

# Neo4j 连接配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "wwj@51816888")

# Redis 缓存 TTL（秒）
CACHE_TTL = 15 * 60  # 15 分钟

# 全局 dish_id 到 name 的映射缓存
dish_id_to_name = {}

# Swagger 文档模型
rec_request = rec_bp.model('RecRequest', {
    'user_id': fields.Integer(required=True, description='用户ID（0-based）'),
    'topk': fields.Integer(default=10, min=1, max=50, description='推荐数量')
})

rec_item = rec_bp.model('RecItem', {
    'dish_id': fields.Integer(description='菜品实体ID'),
    'dish_name': fields.String(description='菜品名称'),
    'price': fields.Integer(description='价格（元）'),
    'tags': fields.List(fields.String, description='口味标签'),
    'ingredients': fields.List(fields.String, description='食材'),
    'photo': fields.String(description='照片文件名'),
    'score': fields.Float(description='推荐分数')
})

rec_response = rec_bp.model('RecResponse', {
    'user_id': fields.Integer(description='用户ID'),
    'topk': fields.Integer(description='实际推荐数量'),
    'from_cache': fields.Boolean(description='是否来自缓存'),
    'recommendations': fields.List(fields.Nested(rec_item))
})


def load_dish_mapping():
    """加载 dish_id 到 name 的映射，建立连续索引与 Neo4j 名称的对应关系"""
    global dish_id_to_name

    try:
        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        # 从 Neo4j 获取所有 Dish 节点的 ID 和名称
        query = """
        MATCH (d:Dish)
        RETURN id(d) as neo_id, d.name as name
        """
        neo_result = graph.run(query).data()

        # 建立 neo4j_id → name 的映射
        neo_id_to_name = {r['neo_id']: r['name'] for r in neo_result if r['name']}

        # 加载 node_map（neo4j_id → continuous_id）
        node_map = pickle.load(open('rec/algo/cache/node_map.pkl', 'rb'))

        # 建立 continuous_id → name 的映射
        # continuous_id 是 node_map 的值，对应嵌入层的索引
        for neo_id, cont_id in node_map.items():
            if neo_id in neo_id_to_name:
                dish_id_to_name[cont_id] = neo_id_to_name[neo_id]

        current_app.logger.info(f"加载了 {len(dish_id_to_name)} 个 dish 映射")

    except Exception as e:
        current_app.logger.error(f"加载 dish 映射失败: {e}")
        # 失败时保持空映射，后续会全部跳过


def get_cache_key(user_id, topk):
    """生成缓存键"""
    key_str = f"rec:{user_id}:{topk}"
    return hashlib.md5(key_str.encode()).hexdigest()


def get_from_cache(redis_client, cache_key):
    """从 Redis 获取缓存"""
    if not redis_client:
        return None
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        current_app.logger.warning(f"Redis 读取失败: {e}")
    return None


def set_cache(redis_client, cache_key, data):
    """写入 Redis 缓存"""
    if not redis_client:
        return False
    try:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(data))
        return True
    except Exception as e:
        current_app.logger.warning(f"Redis 写入失败: {e}")
    return False


def get_dish_info_by_names(dish_names):
    """从 Neo4j 按名称查询菜品详细信息"""
    if not dish_names:
        return {}

    graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

    query = """
    MATCH (d:Dish)
    WHERE d.name IN $dish_names
    OPTIONAL MATCH (d)-[:HAS_TAG]->(t:Tag)
    OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
    RETURN d.name as name, 
           d.price as price,
           d.file as photo,
           collect(DISTINCT t.name) as tags,
           collect(DISTINCT i.name) as ingredients
    """

    result = graph.run(query, dish_names=list(dish_names)).data()

    info_map = {}
    for record in result:
        name = record['name']
        if name:  # 确保名称不为空
            info_map[name] = {
                'name': name,
                'price': record['price'] or 0,
                'photo': record['photo'] or '',
                'tags': [t for t in record['tags'] if t],
                'ingredients': [i for i in record['ingredients'] if i]
            }

    return info_map


@rec_bp.route("/")
class Recommend(Resource):
    @rec_bp.expect(rec_request)
    @rec_bp.marshal_with(rec_response)
    def post(self):
        data = rec_bp.payload
        user_id = data.get('user_id')
        topk = data.get('topk', 10)

        # 参数校验
        if user_id is None or not (0 <= user_id < n_users):
            rec_bp.abort(400, f"无效user_id: {user_id}，有效范围 0-{n_users - 1}")

        # 获取 Redis 客户端（从 extensions.py）
        from app.extensions import redis_client

        # 生成缓存键
        cache_key = get_cache_key(user_id, topk)

        # 尝试读取缓存
        cached_result = get_from_cache(redis_client, cache_key)
        if cached_result:
            cached_result['from_cache'] = True
            return cached_result

        # 缓存未命中，执行推理
        cache_dir = os.path.join(os.path.dirname(__file__), '../algo/cache')
        try:
            ent_emb.load_state_dict(torch.load(
                os.path.join(cache_dir, 'ent_emb.pth'),
                map_location=device
            ))
            ent_emb.eval()
        except FileNotFoundError:
            rec_bp.abort(500, "模型文件未找到，请先运行 ucpr_light.py 训练")

        # 加载 dish 映射（首次调用）
        global dish_id_to_name
        if not dish_id_to_name:
            load_dish_mapping()

        # 推理
        n_items = ent_emb.weight.shape[0] - n_users
        with torch.no_grad():
            user_vec = ent_emb(torch.LongTensor([user_id]))
            all_scores = torch.sum(user_vec + ent_emb.weight[n_users:], dim=1)
            actual_topk = min(topk * 3, n_items)  # 多取一些，过滤后可能不足
            topk_values, topk_indices = torch.topk(all_scores, actual_topk)

        # 获取推荐菜品的名称列表（通过映射）
        dish_names = []
        score_map = {}  # name -> score

        for idx, score in zip(topk_indices.cpu().numpy(), topk_values.numpy()):
            cont_id = int(idx) + n_users
            name = dish_id_to_name.get(cont_id)

            # 跳过无效映射
            if not name or '菜品_' in name or name.startswith('菜品'):
                continue

            dish_names.append(name)
            score_map[name] = float(score)

            if len(dish_names) >= topk * 2:  # 多取一些备用
                break

        # 查询 Neo4j 获取详细信息
        dish_info = get_dish_info_by_names(dish_names)

        # 组装结果（严格过滤）
        recommendations = []
        for name in dish_names:
            if name not in dish_info:
                continue

            info = dish_info[name]

            # 再次检查数据完整性
            if not info['name'] or info['price'] == 0:
                continue

            # 查找对应的 continuous_id（用于返回 dish_id）
            cont_id = None
            for cid, cname in dish_id_to_name.items():
                if cname == name:
                    cont_id = cid
                    break

            recommendations.append({
                'dish_id': cont_id or 0,
                'dish_name': info['name'],
                'price': info['price'],
                'tags': info['tags'],
                'ingredients': info['ingredients'],
                'photo': info['photo'],
                'score': score_map.get(name, 0.0)
            })

            if len(recommendations) >= topk:
                break

        result = {
            'user_id': user_id,
            'topk': len(recommendations),
            'from_cache': False,
            'recommendations': recommendations
        }

        # 写入缓存
        set_cache(redis_client, cache_key, result)

        # 记录日志
        if len(recommendations) < topk:
            current_app.logger.warning(f"推荐数量不足：请求 {topk}，实际返回 {len(recommendations)}")

        return result