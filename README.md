campus-food-kg-rec/
├── .venv/                          # Python虚拟环境
├── .gitignore                      # Git忽略配置
├── requirements.txt                # Python依赖
├── run.py                          # Flask应用入口
├── test_path.py                    # 路径采样测试脚本
├── check_group.py                  # 用户分组查询脚本
├── analyze_experiment.py           # A/B测试数据分析
├── test_optimization.py            # 算法优化测试
├── batch_feedback.py               # 批量反馈提交（新增）
│
├── app/                            # Flask后端应用
│   ├── __init__.py                 # 应用工厂函数
│   ├── config.py                   # 配置类
│   ├── extensions.py               # 扩展实例（JWT/Redis）
│   └── api/                        # RESTful API模块
│       ├── __init__.py
│       ├── hello.py                # 健康检查
│       ├── auth.py                 # JWT认证（修复字符串identity）
│       ├── dish.py                 # 菜品详情（路径解释）
│       └── feedback.py             # 用户反馈收集
│
├── data/                           # 数据层
│   ├── csv/                        # 原始菜品数据（13批次）
│   │   ├── batch1_50.csv ~ batch_new_07.csv
│   ├── raw/                        # 菜品照片
│   ├── menu.json                   # 结构化菜品数据
│   ├── test_users.json             # 30个测试用户
│   └── experiment/                 # A/B测试实验数据
│       ├── ab_test_config.json     # 实验配置（A组15人/B组15人）
│       ├── user_group_map.json     # 用户分组映射
│       ├── feedback_log.jsonl      # 用户反馈日志（42条）
│       └── analysis_report.json    # 实验分析报告
│
├── docs/                           # 文档资料
│   └── 菜单标注模板.xlsx
│
├── frontend/                       # Vue3前端
│   ├── node_modules/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── views/                  # 页面视图
│   │   │   ├── HomeView.vue        # 推荐首页（A/B测试）
│   │   │   ├── DishDetail.vue      # 详情页（路径可视化+反馈）
│   │   │   ├── Login.vue           # 登录/注册
│   │   │   ├── History.vue         # 历史记录
│   │   │   └── Profile.vue         # 个人中心
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── rec/                            # 推荐算法层
│   ├── algo/                       # 算法实现
│   │   ├── cache/                  # 训练缓存
│   │   │   ├── ent_emb.pth         # 旧实体嵌入
│   │   │   ├── rel_emb.pth         # 旧关系嵌入
│   │   │   ├── ent_emb_bpr.pth     # BPR实体嵌入（新增）
│   │   │   ├── rel_emb_bpr.pth     # BPR关系嵌入（新增）
│   │   │   ├── node_map.pkl        # 节点ID映射（1666节点）
│   │   │   ├── kg_triplet.csv      # 图谱三元组
│   │   │   └── samples.csv         # 训练样本
│   │   ├── neo2dgl.py              # Neo4j→DGL转换
│   │   ├── sample_maker.py         # 样本生成
│   │   ├── ucpr_light.py           # UCPR-BPR实现（优化后）
│   │   └── path_sampler.py         # 路径采样（3跳路径）
│   ├── api/
│   │   └── rec_api_stub.py         # 推荐API（A/B分组逻辑）
│   └── eval/
│       ├── eval.py                 # 离线评估（HR/NDCG/MRR）
│       └── eval_results.json       # 评估结果（新增）
│
└── scripts/                        # 数据处理脚本
    ├── excel2json.py
    ├── json2neo4j.py
    ├── test_neo4j.py
    └── init_users.py
