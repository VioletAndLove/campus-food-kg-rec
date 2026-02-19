# =============================================================================
# 功能：健康检查接口，验证 API 服务正常运行
# 归属：week7-8 服务层任务（RESTful API 基础）
# 上游：Flask-RESTX Namespace, Resource
# 下游：Swagger UI 文档、前端/客户端健康检测
# =============================================================================

from flask_restx import Namespace, Resource
# Namespace: 命名空间，用于组织相关 API 端点（对应 Swagger 的 tag）
# Resource: 资源类基类，每个类对应一个 REST 资源，自动映射 HTTP 方法


hello_bp = Namespace("hello", description="健康检查")
# 创建命名空间实例：
# - "hello": URL 前缀 /hello/，Swagger 中显示为分组标签
# - description: Swagger 文档中的描述文本

@hello_bp.route("/")
# 路由装饰器：定义端点 URL
# - "/": 相对路径，完整 URL 为 /hello/（因命名空间已带前缀）
# - 等价于 @app.route('/hello/')
class Hello(Resource):  # 继承 Resource 类，Flask-RESTX 自动处理请求分发
    def get(self):
        return {"msg": "hello campus food kg rec 🍔"}, 200
    # 定义 GET 方法处理函数
    # 方法名小写对应 HTTP 方法：get, post, put, delete 等
    # 返回元组：(响应数据, HTTP 状态码)
    # - 响应数据: dict 自动序列化为 JSON
    # - 200: HTTP OK，标准成功状态码
    #
    # 功能：最简单的健康检查，确认服务存活
    # 访问：curl http://localhost:5000/hello/
    # 响应：{"msg": "hello campus food kg rec 🍔