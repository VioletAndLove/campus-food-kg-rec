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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from algo.ucpr_light import ent_emb, n_users, EMB, device
from algo.path_sampler import PathSampler

rec_bp = Namespace("rec", description="菜品推荐服务")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "wwj@51816888")
)

CACHE_TTL = 15 * 60
dish_id_to_name = {}

# 加载 A/B 测试分组配置
try:
    with open('data/experiment/user_group_map.json', 'r', encoding='utf-8') as f:
        user_group_map = json.load(f)
    print(f"[REC] 加载 A/B 分组配置: {len(user_group_map)} 个用户", flush=True)
except Exception as e:
    print(f"[REC] 加载 A/B 分组配置失败: {e}", flush=True)
    user_group_map = {}

rec_request = rec_bp.model('RecRequest', {
    'user_id': fields.Integer(required=True, description='用户ID'),
    'topk': fields.Integer(default=10, min=1, max=50, description='推荐数量')
})

rec_item = rec_bp.model('RecItem', {
    'dish_id': fields.Integer(description='菜品实体ID'),
    'dish_name': fields.String(description='菜品名称'),
    'price': fields.Integer(description='价格'),
    'tags': fields.List(fields.String, description='口味标签'),
    'ingredients': fields.List(fields.String, description='食材'),
    'photo': fields.String(description='照片文件名'),
    'score': fields.Float(description='推荐分数'),
    'explanation': fields.String(description='推荐解释'),
    'paths': fields.List(fields.Raw, description='推理路径列表')
})

rec_response = rec_bp.model('RecResponse', {
    'user_id': fields.Integer(description='用户ID'),
    'topk': fields.Integer(description='实际推荐数量'),
    'from_cache': fields.Boolean(description='是否来自缓存'),
    'experiment_group': fields.String(description='A/B测试分组: A(实验组)或B(对照组)'),
    'show_explanation': fields.Boolean(description='是否显示解释'),
    'recommendations': fields.List(fields.Nested(rec_item))
})


def get_user_group(user_id):
    """获取用户A/B测试分组，默认B组"""
    return user_group_map.get(str(user_id), 'B')


def load_dish_mapping():
    global dish_id_to_name
    try:
        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
        query = "MATCH (d:Dish) RETURN id(d) as neo_id, d.name as name"
        neo_result = graph.run(query).data()
        neo_id_to_name = {r['neo_id']: r['name'] for r in neo_result if r['name']}
        node_map = pickle.load(open('rec/algo/cache/node_map.pkl', 'rb'))
        for neo_id, cont_id in node_map.items():
            if neo_id in neo_id_to_name:
                dish_id_to_name[cont_id] = neo_id_to_name[neo_id]
        current_app.logger.info(f"加载了 {len(dish_id_to_name)} 个 dish 映射")
    except Exception as e:
        current_app.logger.error(f"加载 dish 映射失败: {e}")


def get_cache_key(user_id, topk):
    key_str = f"rec:{user_id}:{topk}"
    return hashlib.md5(key_str.encode()).hexdigest()


def get_from_cache(redis_client, cache_key):
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
    if not redis_client:
        return False
    try:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(data))
        return True
    except Exception as e:
        current_app.logger.warning(f"Redis 写入失败: {e}")
    return False


def get_dish_info_by_names(dish_names):
    if not dish_names:
        return {}
    graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
    query = """
    MATCH (d:Dish) WHERE d.name IN $dish_names
    OPTIONAL MATCH (d)-[:HAS_TAG]->(t:Tag)
    OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
    RETURN d.name as name, d.price as price, d.file as photo,
           collect(DISTINCT t.name) as tags,
           collect(DISTINCT i.name) as ingredients
    """
    result = graph.run(query, dish_names=list(dish_names)).data()
    info_map = {}
    for record in result:
        name = record['name']
        if name:
            info_map[name] = {
                'name': name,
                'price': record['price'] or 0,
                'photo': record['photo'] or '',
                'tags': [t for t in record['tags'] if t],
                'ingredients': [i for i in record['ingredients'] if i]
            }
    return info_map


def format_path_explanation(paths, target_name):
    if not paths:
        return "基于您的历史偏好推荐"
    explanations = []
    for path in paths[:2]:
        if len(path) >= 2:
            rels = [p[0] for p in path]
            if 'HAS_TAG' in rels:
                tag = path[0][1] if len(path) > 0 else ""
                explanations.append(f"同属「{tag}」口味")
            elif 'CONTAINS' in rels:
                ing = path[0][1] if len(path) > 0 else ""
                explanations.append(f"都含有「{ing}」食材")
    if explanations:
        return "，".join(explanations) + f" → {target_name}"
    return "基于知识图谱路径推理推荐"


@rec_bp.route("/")
class Recommend(Resource):
    @rec_bp.expect(rec_request)
    @rec_bp.marshal_with(rec_response)
    def post(self):
        data = rec_bp.payload
        user_id = data.get('user_id')
        topk = data.get('topk', 10)

        if user_id is None or not (0 <= user_id < n_users):
            rec_bp.abort(400, f"无效user_id: {user_id}")

        # 获取A/B测试分组
        group = get_user_group(user_id)
        show_explanation = (group == 'A')  # A组显示解释，B组不显示

        from app.extensions import redis_client
        cache_key = get_cache_key(user_id, topk)
        cached_result = get_from_cache(redis_client, cache_key)

        if cached_result:
            cached_result['from_cache'] = True
            cached_result['experiment_group'] = group
            cached_result['show_explanation'] = show_explanation
            return cached_result

        cache_dir = os.path.join(os.path.dirname(__file__), '../algo/cache')
        try:
            ent_emb.load_state_dict(torch.load(
                os.path.join(cache_dir, 'ent_emb.pth'),
                map_location=device
            ))
            ent_emb.eval()
        except FileNotFoundError:
            rec_bp.abort(500, "模型文件未找到")

        global dish_id_to_name
        if not dish_id_to_name:
            load_dish_mapping()

        path_sampler = PathSampler()

        n_items = ent_emb.weight.shape[0] - n_users
        with torch.no_grad():
            user_vec = ent_emb(torch.LongTensor([user_id]))
            all_scores = torch.sum(user_vec + ent_emb.weight[n_users:], dim=1)
            actual_topk = min(topk * 3, n_items)
            topk_values, topk_indices = torch.topk(all_scores, actual_topk)

        dish_names = []
        score_map = {}
        for idx, score in zip(topk_indices.cpu().numpy(), topk_values.numpy()):
            cont_id = int(idx) + n_users
            name = dish_id_to_name.get(cont_id)
            if not name or '菜品_' in name or name.startswith('菜品'):
                continue
            dish_names.append(name)
            score_map[name] = float(score)
            if len(dish_names) >= topk * 2:
                break

        dish_info = get_dish_info_by_names(dish_names)

        recommendations = []
        for name in dish_names:
            if name not in dish_info:
                continue
            info = dish_info[name]
            if not info['name'] or info['price'] == 0:
                continue

            cont_id = None
            for cid, cname in dish_id_to_name.items():
                if cname == name:
                    cont_id = cid
                    break

            # A/B测试：A组采样路径并显示解释，B组跳过路径采样
            if show_explanation:
                paths = path_sampler.sample_paths_for_user_item(user_id, name)
                explanation = format_path_explanation(paths, name)
                path_data = [
                    {
                        'relations': [p[0] for p in path],
                        'entities': [p[1] for p in path],
                        'pattern': path_sampler.get_path_pattern(path)
                    } for path in paths[:3]
                ]
            else:
                paths = []
                explanation = "基于知识图谱推荐"
                path_data = []

            recommendations.append({
                'dish_id': cont_id or 0,
                'dish_name': info['name'],
                'price': info['price'],
                'tags': info['tags'],
                'ingredients': info['ingredients'],
                'photo': info['photo'],
                'score': score_map.get(name, 0.0),
                'explanation': explanation,
                'paths': path_data
            })

            if len(recommendations) >= topk:
                break

        result = {
            'user_id': user_id,
            'topk': len(recommendations),
            'from_cache': False,
            'experiment_group': group,
            'show_explanation': show_explanation,
            'recommendations': recommendations
        }

        set_cache(redis_client, cache_key, result)

        if len(recommendations) < topk:
            current_app.logger.warning(f"推荐数量不足：请求 {topk}，实际返回 {len(recommendations)}")

        return result