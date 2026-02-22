from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json
import os

feedback_bp = Namespace("feedback", description="用户反馈收集")

feedback_model = feedback_bp.model('Feedback', {
    'dish_id': fields.Integer(required=True),
    'rating': fields.Integer(min=1, max=5, required=True, description='满意度 1-5'),
    'clicked': fields.Boolean(default=True, description='是否点击'),
    'comment': fields.String(description='可选评论')
})


@feedback_bp.route("/")
class Feedback(Resource):
    @jwt_required()
    @feedback_bp.expect(feedback_model)
    def post(self):
        user_id = get_jwt_identity()
        data = feedback_bp.payload

        # 加载实验分组
        group = 'unknown'
        try:
            with open('data/experiment/user_group_map.json', 'r') as f:
                group_map = json.load(f)
                group = group_map.get(str(user_id), 'unknown')
        except:
            pass

        # 记录反馈
        record = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'group': group,
            'dish_id': data['dish_id'],
            'rating': data['rating'],
            'clicked': data.get('clicked', True),
            'comment': data.get('comment', '')
        }

        # 追加写入文件（简单实现，生产环境用数据库）
        log_file = 'data/experiment/feedback_log.jsonl'
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

        return {'msg': '反馈已记录', 'group': group}