from flask_restx import Namespace, Resource

hello_bp = Namespace("hello", description="健康检查")

@hello_bp.route("/")
class Hello(Resource):
    def get(self):
        return {"msg": "hello campus food kg rec 🍔"}, 200