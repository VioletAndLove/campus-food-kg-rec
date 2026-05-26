from flask_restx import Namespace, Resource, fields
from flask import session
from py2neo import Graph
import os
import pickle
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rec.algo.path_sampler import PathSampler

dish_bp = Namespace("dish", description="菜品详情、搜索与评论")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "wwj@51816888")
)

try:
    node_map = pickle.load(open('rec/algo/cache/node_map.pkl', 'rb'))
    cont_to_neo = {int(v): int(k) for k, v in node_map.items()}
    neo_to_cont = {int(k): int(v) for k, v in node_map.items()}
except Exception as e:
    print(f"[DISH] 加载 node_map 失败: {e}")
    cont_to_neo = {}
    neo_to_cont = {}

# API模型
search_request = dish_bp.model('SearchRequest', {
    'query': fields.String(description='搜索关键词'),
    'tags': fields.List(fields.String, description='口味标签筛选'),
    'ingredients': fields.List(fields.String, description='食材筛选'),
    'min_price': fields.Integer(default=0, description='最低价格'),
    'max_price': fields.Integer(default=100, description='最高价格')
})

comment_request = dish_bp.model('CommentRequest', {
    'rating': fields.Integer(required=True, min=1, max=5, description='评分1-5'),
    'content': fields.String(required=True, description='评论内容'),
    'is_anonymous': fields.Boolean(default=False, description='是否匿名')
})

comment_item = dish_bp.model('CommentItem', {
    'comment_id': fields.Integer,
    'user_id': fields.Integer,
    'username': fields.String,
    'rating': fields.Integer,
    'content': fields.String,
    'created_at': fields.String,
    'is_anonymous': fields.Boolean,
    'likes': fields.Integer,
    'is_liked': fields.Boolean
})

dish_detail = dish_bp.model('DishDetail', {
    'dish_id': fields.Integer,
    'name': fields.String,
    'price': fields.Integer,
    'photo': fields.String,
    'tags': fields.List(fields.String),
    'ingredients': fields.List(fields.String),
    'explanation': fields.String,
    'paths': fields.List(fields.Raw),
    'avg_rating': fields.Float,
    'total_comments': fields.Integer,
    'comments': fields.List(fields.Nested(comment_item))
})


@dish_bp.route("/search")
class DishSearch(Resource):
    @dish_bp.expect(search_request)
    def post(self):
        """多条件搜索菜品"""
        data = dish_bp.payload or {}
        query = data.get('query', '').strip().lower()
        tags = data.get('tags', [])
        ingredients = data.get('ingredients', [])
        min_price = data.get('min_price', 0)
        max_price = data.get('max_price', 100)

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        cypher = """
        MATCH (d:Dish)
        WHERE d.price >= $min_price AND d.price <= $max_price
        """

        params = {
            'min_price': min_price,
            'max_price': max_price
        }

        if query:
            cypher += " AND (toLower(d.name) CONTAINS $query OR d.name CONTAINS $query)"
            params['query'] = query

        cypher += """
        OPTIONAL MATCH (d)-[:HAS_TAG]->(t:Tag)
        OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
        WITH d, collect(DISTINCT t.name) as tags, collect(DISTINCT i.name) as ingredients
        """

        if tags:
            cypher += " WHERE ALL(tag IN $tags WHERE tag IN tags)"
            params['tags'] = tags

        if ingredients:
            cypher += " AND ALL(ing IN $ingredients WHERE ing IN ingredients)" if tags else " WHERE ALL(ing IN $ingredients WHERE ing IN ingredients)"
            params['ingredients'] = ingredients

        cypher += """
        RETURN id(d) as neo_id, d.name as name, d.price as price, d.file as photo,
               tags, ingredients
        LIMIT 50
        """

        results = graph.run(cypher, **params).data()

        items = []
        for record in results:
            neo_id = record['neo_id']
            cont_id = neo_to_cont.get(neo_id, neo_id)

            items.append({
                'dish_id': int(cont_id),  # 确保是整数
                'dish_name': record['name'],
                'price': record['price'] or 0,
                'tags': [t for t in record['tags'] if t],
                'ingredients': [i for i in record['ingredients'] if i],
                'photo': record['photo'] or ''
            })

        return {
            'total': len(items),
            'results': items
        }


@dish_bp.route("/filters")
class DishFilters(Resource):
    def get(self):
        """获取所有可用的筛选选项（标签和食材）"""
        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        # 获取所有标签
        tags_query = "MATCH (t:Tag) RETURN t.name as name ORDER BY t.name"
        tags_result = graph.run(tags_query).data()

        # 获取所有食材
        ingredients_query = "MATCH (i:Ingredient) RETURN i.name as name ORDER BY i.name LIMIT 50"
        ingredients_result = graph.run(ingredients_query).data()

        return {
            'tags': [r['name'] for r in tags_result if r['name']],
            'ingredients': [r['name'] for r in ingredients_result if r['name']]
        }


@dish_bp.route("/<int:dish_id>")
class DishDetail(Resource):
    @dish_bp.marshal_with(dish_detail)
    def get(self, dish_id):
        """获取菜品详情（含评论）"""
        print(f"[DEBUG] 获取菜品详情, dish_id={dish_id}, type={type(dish_id)}")

        neo_id = cont_to_neo.get(int(dish_id))
        print(f"[DEBUG] 映射到 neo_id={neo_id}")

        if not neo_id:
            dish_bp.abort(404, f"找不到 dish_id {dish_id}")

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        # 获取菜品基本信息
        query = """
        MATCH (d:Dish)
        WHERE id(d) = $neo_id
        OPTIONAL MATCH (d)-[:HAS_TAG]->(t:Tag)
        OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
        RETURN d.name as name, 
               d.price as price, 
               d.file as photo,
               collect(DISTINCT t.name) as tags,
               collect(DISTINCT i.name) as ingredients
        """
        result = graph.run(query, neo_id=int(neo_id)).data()

        if not result or not result[0].get('name'):
            dish_bp.abort(404, "菜品未找到")

        data = result[0]

        # 获取评论
        comments_query = """
        MATCH (d:Dish)<-[r:RATED]-(u:User)
        WHERE id(d) = $neo_id
        RETURN u.user_id as user_id, u.username as username,
               r.rating as rating, r.content as content,
               r.created_at as created_at, r.is_anonymous as is_anonymous,
               r.likes as likes, id(r) as rid,
               r.liked_by as liked_by
        ORDER BY r.created_at DESC
        LIMIT 20
        """
        comments_result = graph.run(comments_query, neo_id=int(neo_id)).data()

        # 计算平均评分
        avg_query = """
        MATCH (d:Dish)<-[r:RATED]-()
        WHERE id(d) = $neo_id
        RETURN avg(r.rating) as avg_rating, count(r) as total
        """
        avg_result = graph.run(avg_query, neo_id=int(neo_id)).data()
        avg_rating = avg_result[0]['avg_rating'] if avg_result else 0
        total_comments = avg_result[0]['total'] if avg_result else 0

        # 获取当前用户（可能未登录）
        user_id = session.get('user_id')

        explanation = "基于知识图谱推荐"
        paths = []

        if user_id is not None:
            sampler = PathSampler()
            paths = sampler.sample_paths_for_user_item(user_id, data['name'])

            if paths:
                patterns = [sampler.get_path_pattern(p) for p in paths]
                if 'HAS_TAG' in str(patterns) and 'CONTAINS' in str(patterns):
                    explanation = f"基于口味标签和食材相似推荐 → {data['name']}"
                elif 'HAS_TAG' in str(patterns):
                    explanation = f"同属口味标签推荐 → {data['name']}"
                elif 'CONTAINS' in str(patterns):
                    explanation = f"含有相似食材推荐 → {data['name']}"

        comments = []
        for r in comments_result:
            liked_by = r.get('liked_by') or []
            liked_by_strs = [str(x) for x in liked_by]
            is_liked = str(user_id) in liked_by_strs if user_id is not None else False
            comments.append({
                'comment_id': abs(int(r['user_id']) * 1000000000 + int(r['rating']) * 1000000 + int(r['rid'])),
                'user_id': r['user_id'],
                'username': '匿名用户' if r.get('is_anonymous') else r['username'],
                'rating': r['rating'],
                'content': r['content'] or '',
                'created_at': str(r['created_at']) if r['created_at'] else '',
                'is_anonymous': r.get('is_anonymous', False),
                'likes': r.get('likes', 0),
                'is_liked': is_liked
            })

        return {
            "dish_id": int(dish_id),
            "name": str(data['name']),
            "price": int(data['price']) if data['price'] else 0,
            "photo": str(data['photo']) if data['photo'] else '',
            "tags": [str(t) for t in data['tags'] if t],
            "ingredients": [str(i) for i in data['ingredients'] if i],
            "explanation": explanation,
            "paths": [
                {
                    "pattern": str(sampler.get_path_pattern(p)) if user_id else "",
                    "relations": [str(rel) for rel, _ in p],
                    "entities": [str(ent) for _, ent in p]
                } for p in paths[:3]
            ] if paths else [],
            "avg_rating": round(float(avg_rating), 2) if avg_rating else 0,
            "total_comments": total_comments,
            "comments": comments
        }


@dish_bp.route("/<int:dish_id>/comment")
class DishComment(Resource):
    @dish_bp.expect(comment_request)
    def post(self, dish_id):
        """提交菜品评论"""
        user_id = session.get('user_id')
        if user_id is None:
            dish_bp.abort(401, "请先登录")

        neo_id = cont_to_neo.get(int(dish_id))
        if not neo_id:
            dish_bp.abort(404, "菜品不存在")

        data = dish_bp.payload
        rating = data.get('rating')
        content = data.get('content', '').strip()
        is_anonymous = data.get('is_anonymous', False)

        if not rating or rating < 1 or rating > 5:
            dish_bp.abort(400, "评分必须在1-5之间")

        if not content or len(content) < 2:
            dish_bp.abort(400, "评论内容至少2个字")

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        # 创建或更新评分关系
        query = """
        MATCH (u:User {user_id: $user_id})
        MATCH (d:Dish) WHERE id(d) = $neo_id
        MERGE (u)-[r:RATED]->(d)
        ON CREATE SET r.rating = $rating, r.content = $content, 
                      r.created_at = datetime(), r.is_anonymous = $is_anonymous,
                      r.likes = 0
        ON MATCH SET r.rating = $rating, r.content = $content,
                     r.created_at = datetime(), r.is_anonymous = $is_anonymous
        RETURN r
        """

        try:
            graph.run(query,
                      user_id=user_id,
                      neo_id=neo_id,
                      rating=rating,
                      content=content,
                      is_anonymous=is_anonymous)

            # 同时更新/创建INTERACTED关系（用于历史记录）
            interact_query = """
            MATCH (u:User {user_id: $user_id})
            MATCH (d:Dish) WHERE id(d) = $neo_id
            MERGE (u)-[r:INTERACTED]->(d)
            ON CREATE SET r.rating = $rating, r.timestamp = datetime()
            ON MATCH SET r.rating = $rating, r.timestamp = datetime()
            """
            graph.run(interact_query, user_id=user_id, neo_id=neo_id, rating=rating)

            return {"msg": "评论提交成功"}, 201

        except Exception as e:
            dish_bp.abort(500, f"评论提交失败: {str(e)}")


@dish_bp.route("/<int:dish_id>/comments")
class DishCommentsList(Resource):
    def get(self, dish_id):
        """获取菜品所有评论（分页）"""
        from flask import request

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        neo_id = cont_to_neo.get(int(dish_id))
        if not neo_id:
            dish_bp.abort(404, "菜品不存在")

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        # 获取评论总数
        count_query = """
        MATCH (d:Dish)<-[r:RATED]-()
        WHERE id(d) = $neo_id
        RETURN count(r) as total
        """
        count_result = graph.run(count_query, neo_id=int(neo_id)).data()
        total = count_result[0]['total'] if count_result else 0

        # 分页获取评论
        skip = (page - 1) * per_page
        comments_query = """
        MATCH (d:Dish)<-[r:RATED]-(u:User)
        WHERE id(d) = $neo_id
        RETURN u.user_id as user_id, u.username as username,
               r.rating as rating, r.content as content,
               r.created_at as created_at, r.is_anonymous as is_anonymous,
               r.likes as likes, id(r) as rid,
               r.liked_by as liked_by
        ORDER BY r.created_at DESC
        SKIP $skip LIMIT $limit
        """
        comments_result = graph.run(comments_query,
                                    neo_id=int(neo_id),
                                    skip=skip,
                                    limit=per_page).data()

        # 获取当前登录用户ID（可能未登录）
        current_user_id = session.get('user_id')

        comments = []
        for r in comments_result:
            liked_by = r.get('liked_by') or []
            liked_by_strs = [str(x) for x in liked_by]
            is_liked = str(current_user_id) in liked_by_strs if current_user_id is not None else False
            comments.append({
                'comment_id': abs(int(r['user_id']) * 1000000000 + int(r['rating']) * 1000000 + int(r['rid'])),
                'user_id': r['user_id'],
                'username': '匿名用户' if r.get('is_anonymous') else r['username'],
                'rating': r['rating'],
                'content': r['content'] or '',
                'created_at': str(r['created_at']) if r['created_at'] else '',
                'is_anonymous': r.get('is_anonymous', False),
                'likes': r.get('likes', 0),
                'is_liked': is_liked
            })

        return {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'comments': comments
        }


@dish_bp.route("/<int:dish_id>/rating-stats")
class DishRatingStats(Resource):
    def get(self, dish_id):
        """获取菜品评分分布统计"""
        neo_id = cont_to_neo.get(int(dish_id))
        if not neo_id:
            dish_bp.abort(404, "菜品不存在")

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)

        stats_query = """
        MATCH (d:Dish)<-[r:RATED]-()
        WHERE id(d) = $neo_id
        RETURN r.rating as rating, count(r) as cnt
        """
        stats_result = graph.run(stats_query, neo_id=int(neo_id)).data()

        stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total = 0
        for row in stats_result:
            rating = int(row['rating'])
            cnt = int(row['cnt'])
            if rating in stats:
                stats[rating] = cnt
                total += cnt

        return {
            'dish_id': dish_id,
            'total': total,
            'stats': stats,
            'avg_rating': round(sum(k * v for k, v in stats.items()) / total, 2) if total > 0 else 0
        }


@dish_bp.route("/<int:dish_id>/comment/<int:comment_id>/like")
class CommentLike(Resource):
    def post(self, dish_id, comment_id):
        """点赞评论"""
        user_id = session.get('user_id')
        if user_id is None:
            dish_bp.abort(401, "请先登录")

        neo_id = cont_to_neo.get(int(dish_id))
        if not neo_id:
            dish_bp.abort(404, "菜品不存在")

        graph = Graph(NEO4J_URI, auth=NEO4J_AUTH)
        user_id_str = str(user_id)

        # 先检查是否已点赞
        check_query = """
        MATCH (d:Dish)<-[r:RATED]-(u:User)
        WHERE id(d) = $neo_id
        WITH r, u
        WHERE abs(u.user_id * 1000000000 + r.rating * 1000000 + id(r)) = $comment_id
        RETURN r.likes as likes, r.liked_by as liked_by, u.user_id as comment_user_id
        """
        check_result = graph.run(check_query, neo_id=int(neo_id), comment_id=int(comment_id)).data()

        if not check_result:
            dish_bp.abort(404, "评论不存在")

        record = check_result[0]
        liked_by = record.get('liked_by') or []
        liked_by_strs = [str(x) for x in liked_by]

        if user_id_str in liked_by_strs:
            dish_bp.abort(400, "您已经点过赞了")

        # 执行点赞
        update_query = """
        MATCH (d:Dish)<-[r:RATED]-(u:User)
        WHERE id(d) = $neo_id
        WITH r, u
        WHERE abs(u.user_id * 1000000000 + r.rating * 1000000 + id(r)) = $comment_id
        SET r.likes = coalesce(r.likes, 0) + 1,
            r.liked_by = coalesce(r.liked_by, []) + $user_id_str
        RETURN r.likes as likes
        """
        result = graph.run(update_query, neo_id=int(neo_id), comment_id=int(comment_id), user_id_str=user_id_str).data()

        return {
            'msg': '点赞成功',
            'likes': result[0]['likes'],
            'comment_id': comment_id
        }