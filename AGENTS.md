# AGENTS.md — 校园美食知识图谱推荐系统

> 本文件面向 AI 编程助手。如果你正在阅读此文件，说明你对本项目一无所知。以下内容全部基于实际代码，不做假设。

---

## 项目概述

本项目是一个**基于知识图谱的校园美食推荐系统**，采用前后端分离架构。核心能力包括：

- 以 Neo4j 构建菜品知识图谱（Dish、Tag、Ingredient、User 等节点及关系）
- 使用 UCPR（User-Controllable Path Reasoning）简化模型，基于 TransE 嵌入 + BPR 损失进行推荐
- 提供可解释推荐路径（2 跳 / 3 跳图谱路径），并支持 A/B 测试对比"有解释" vs "无解释"推荐效果
- 用户可搜索菜品、评分、查看历史记录、管理个人口味画像

代码注释与文档以**中文**为主。

---

## 技术栈

### 后端
- **Python 3.x**
- **Flask 2.3.3** + **Flask-RESTX 1.3.0**（RESTful API + Swagger 文档）
- **Flask-CORS**（跨域支持，开发环境允许 `localhost:5173`）
- **Flask 原生 Session**（文件系统存储，7 天有效期）
- **py2neo 2021.2.4**（Neo4j 图数据库驱动）
- **redis 5.0.1**（推荐结果缓存，默认 TTL 15 分钟）
- **PyTorch**（UCPR 模型训练与推理）
- **pandas / numpy / sklearn**（数据处理与离线评估）
- **gunicorn 21.2.0**（生产服务器）

### 前端
- **Vue 3**（Composition API + `<script setup>`）
- **Vite 7.x**（构建工具，开发端口 5173）
- **Element Plus 2.x**（UI 组件库）
- **Vue Router 4.x**
- **Axios**（HTTP 请求，`withCredentials: true` 以支持 Session Cookie）
- **Pinia 3.x**（已安装，但实际使用 `provide/inject` 管理全局认证状态）

### 数据层
- **Neo4j**（知识图谱，默认 `bolt://localhost:7687`）
- **Redis**（缓存，默认 `redis://localhost:6379/0`）
- **JSON / CSV / pickle**（本地实验数据与模型缓存）

---

## 项目结构

```
├── app/                        # Flask 应用（工厂模式）
│   ├── __init__.py             # create_app()：注册命名空间、CORS、静态文件路由
│   ├── config.py               # Config 类：Neo4j / Redis / Session 配置
│   ├── extensions.py           # Redis 客户端（延迟初始化）
│   └── api/                    # RESTX 命名空间（Namespace）
│       ├── auth.py             # 注册 / 登录 / 登出 / 状态查询（Session + MD5）
│       ├── dish.py             # 菜品搜索 / 详情 / 评论 / 筛选条件
│       ├── feedback.py         # A/B 测试反馈收集（写入 JSONL）
│       ├── history.py          # 用户历史交互记录（分页 / 删除）
│       ├── profile.py          # 用户画像 / 口味分析 / 价格偏好统计
│       └── hello.py            # 测试用 Hello World
├── rec/                        # 推荐系统
│   ├── algo/                   # 算法模块
│   │   ├── ucpr_light.py       # UCPR-BPR 模型定义与训练脚本
│   │   ├── path_sampler.py     # Neo4j 路径采样器（2 跳 / 3 跳）+ 多样性计算
│   │   ├── neo2dgl.py          # 将 Neo4j 导出为三元组 CSV 与节点映射
│   │   └── sample_maker.py     # 生成训练样本（正例 + 负采样）
│   ├── api/
│   │   └── rec_api_stub.py     # 推荐 API：加载模型、Redis 缓存、A/B 分组、路径解释
│   └── eval/
│       └── eval.py             # 离线评测：HR@K / NDCG@K / MRR / Diversity
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── main.js             # Axios / Element Plus / 图标注册
│   │   ├── App.vue             # 全局认证状态注入（provide/inject）
│   │   ├── router/index.js     # 路由配置
│   │   ├── views/              # 页面级组件
│   │   │   ├── HomeView.vue    # 首页：搜索 + 推荐列表
│   │   │   ├── Login.vue       # 登录 / 注册页
│   │   │   ├── DishDetail.vue  # 菜品详情 + 评论
│   │   │   ├── History.vue     # 历史记录
│   │   │   ├── Profile.vue     # 个人中心
│   │   │   └── AboutView.vue   # 关于页
│   │   └── components/         # 可复用组件（DishCard 等）
│   ├── package.json
│   └── vite.config.js          # 代理 /api 与 /static 到 localhost:5000
├── scripts/                    # 运维与数据脚本
│   ├── excel2json.py           # Excel 菜单 -> data/menu.json
│   ├── json2neo4j.py           # menu.json -> Neo4j 知识图谱
│   ├── init_users.py           # 批量注册测试用户并生成交互记录
│   ├── prepare_ab_test.py      # A/B 测试分组配置生成
│   └── test_neo4j.py           # Neo4j 连通性测试
├── data/                       # 数据目录
│   ├── menu.json               # 菜品源数据
│   ├── test_users.json         # 测试用户清单
│   ├── raw/                    # 菜品照片
│   ├── csv/                    # CSV 中间数据
│   └── experiment/             # A/B 测试实验数据
│       ├── ab_test_config.json
│       ├── user_group_map.json
│       ├── feedback_log.jsonl
│       └── analysis_report.json
├── run.py                      # 开发入口：create_app().run(debug=True, port=5000)
├── requirements.txt            # Python 依赖
└── analyze_experiment.py       # A/B 测试反馈数据分析脚本
```

---

## 启动与构建命令

### 环境前提
1. 启动 **Neo4j**（默认 `bolt://localhost:7687`，用户名 `neo4j`，密码可通过环境变量 `NEO4J_PASSWORD` 覆盖）
2. 启动 **Redis**（默认 `localhost:6379`）
3. 构建知识图谱（首次运行）：
   ```bash
   python scripts/json2neo4j.py
   ```

### 后端（开发）
```bash
python run.py
# 或
flask run
```
- 默认端口 `5000`
- 自动加载 Swagger 文档：`http://localhost:5000/api/doc/`

### 后端（生产）
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### 前端（开发）
```bash
cd frontend
npm install
npm run dev
```
- 默认端口 `5173`
- Vite 代理已将 `/api` 与 `/static` 转发到 `localhost:5000`

### 前端（生产构建）
```bash
cd frontend
npm run build
```

### 代码检查（前端）
```bash
cd frontend
npm run lint        # 先运行 oxlint --fix，再运行 eslint --fix
```

---

## 核心模块说明

### 1. 认证机制（`app/api/auth.py`）
- 使用 **Flask Session**（文件系统存储，Cookie  signed with `SECRET_KEY`）
- 密码使用 **MD5** 哈希（注意：这是项目现状，并非安全最佳实践）
- 用户上限 500 人（硬编码在 `create_user`）
- 前端通过 `axios.defaults.withCredentials = true` 携带 Cookie

### 2. 推荐算法（`rec/algo/` + `rec/api/rec_api_stub.py`）
- **模型**：`UCPRModel`（PyTorch `nn.Module`），TransE 风格嵌入 + BPR 损失
- **训练**：`python rec/algo/ucpr_light.py`，输出 `rec/algo/cache/ent_emb_bpr.pth` / `rel_emb_bpr.pth`
- **推理**：`rec_api_stub.py` 加载模型，为每个用户对全部物品打分，取 Top-K
- **缓存**：推荐结果写入 Redis，TTL 15 分钟
- **ID 映射**：通过 `rec/algo/cache/node_map.pkl` 在 Neo4j 原生 ID（`id(d)`）与连续模型 ID 之间转换

### 3. 路径解释（`rec/algo/path_sampler.py`）
- 从用户历史交互菜品出发，采样到目标菜品的 2 跳（`Dish-Tag-Dish` / `Dish-Ingredient-Dish`）或 3 跳路径
- 多样性指标：`compute_path_diversity_v2()` 综合 Simpson's Index 与模式多样性
- A 组用户（实验组）在推荐结果中展示解释路径；B 组（对照组）隐藏

### 4. A/B 测试流程
1. 运行 `scripts/init_users.py` 生成 30 个测试用户
2. 运行 `scripts/prepare_ab_test.py` 随机分 A/B 组（种子 42），生成 `data/experiment/user_group_map.json`
3. 用户在前端提交反馈（评分 / 评论）→ 后端写入 `feedback_log.jsonl`
4. 运行 `python analyze_experiment.py` 分析组间差异

---

## 代码风格与约定

### 文件头注释
几乎每个 Python 文件顶部都有标准化的中文注释块：
```python
# =============================================================================
# 功能：<一句话描述>
# 归属：<weekX 任务归属>
# 上游：<依赖输入>
# 下游：<消费输出>
# =============================================================================
```
**请勿删除或随意修改这些注释块**，它们是模块间依赖的重要说明。

### 命名与语言
- Python：模块名小写 + 下划线；类名大驼峰；函数/变量小写 + 下划线
- Vue：组件名大驼峰（如 `DishCard.vue`）；组合式 API 优先使用 `<script setup>`
- 字符串：对外 API 返回中文；数据库 Cypher 查询中使用中文实体名（如 `Tag.name`）

### 硬编码注意事项
- Neo4j 默认密码 `wwj@51816888` 硬编码在多处（`config.py`、各 API 模块、`scripts/`、`rec/algo/`）
- Redis URL、用户上限（500）、BPR 超参数（`EPOCH=50, EMB=32`）均为硬编码
- 修改时请全局搜索，避免遗漏

---

## 测试策略

本项目**没有使用 pytest / unittest 等自动化测试框架**，测试以脚本和手动验证为主：

1. **数据脚本验证**
   - `scripts/test_neo4j.py`：检查 Neo4j 连通性
   - `scripts/json2neo4j.py`：构建图谱后输出节点数
2. **算法离线评测**
   - `rec/eval/eval.py`：计算 HR@10 / NDCG@10 / MRR / Diversity，结果写入 `rec/eval/eval_results.json`
3. **用户模拟测试**
   - `scripts/init_users.py`：创建 30 个测试用户并注入交互数据
   - 登录 `test_user_000` ~ `test_user_029` 进行端到端验证
4. **A/B 测试分析**
   - `analyze_experiment.py`：统计两组满意度均值、标准差、分布

---

## 安全注意事项

- **密码哈希**：当前使用 MD5，强度不足。若涉及真实用户，建议迁移至 `bcrypt` 或 `argon2`
- **凭证泄露**：Neo4j 密码明文硬编码在多个源文件中，生产环境务必改用环境变量（`.env`）
- **Session 安全**：`SECRET_KEY` 在 `config.py` 中有默认值 `dev-secret-key-2024`，生产环境必须覆盖
- **CORS**：开发配置允许 `http://localhost:5173`，生产环境应收紧域名白名单
- **用户上限**：注册接口限制最多 500 用户，防止无限注册
- **SQL/NoSQL 注入**：Cypher 查询均使用参数化（`$param`），当前未发现拼接注入风险

---

## 常见修改场景指引

| 场景 | 相关文件 |
|------|----------|
| 新增后端 API | `app/api/<module>.py` → 在 `app/__init__.py` 注册命名空间 |
| 修改推荐逻辑 | `rec/api/rec_api_stub.py`（推理）、`rec/algo/ucpr_light.py`（训练） |
| 调整路径解释 | `rec/algo/path_sampler.py` |
| 修改前端页面 | `frontend/src/views/*.vue` |
| 新增前端路由 | `frontend/src/router/index.js` |
| 导入新菜品数据 | `scripts/excel2json.py` → `scripts/json2neo4j.py` |
| 修改 Neo4j/Redis 连接 | `app/config.py`（同时检查各模块中的硬编码 fallback） |
| A/B 测试新实验 | 复制 `scripts/prepare_ab_test.py` 逻辑，更新分组文件路径 |

---

## 依赖文件清单

运行前必须确保以下文件/服务就位：

- **Neo4j** 数据库已启动且可连接
- **Redis** 已启动
- `data/menu.json`（菜品数据）
- `rec/algo/cache/node_map.pkl`（由 `neo2dgl.py` 生成）
- `rec/algo/cache/ent_emb_bpr.pth` + `rel_emb_bpr.pth`（由 `ucpr_light.py` 训练生成）
- `rec/algo/cache/kg_triplet.csv` + `samples.csv`（训练数据）

缺失模型缓存会导致推荐 API 返回 500（`FileNotFoundError: 模型文件未找到`）。
