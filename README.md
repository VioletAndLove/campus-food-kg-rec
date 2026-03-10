Rec-kg启动指令

终端运行neo4j.bat console

# 确保在 PyCharm Terminal 或 cmd 中，位于项目根目录
cd D:\PycharmProjects\campus-food-kg-rec

# 执行转换
python scripts/excel2json.py

# 执行导入
python scripts/json2neo4j.py

#Neo4j → 三元组（导出训练格式）
python rec/algo/neo2dgl.py

#生成训练样本
python rec/algo/sample_maker.py

训练 UCPR 模型
python rec/algo/ucpr_light.py

检测路径多样性
python rec/algo/path_sampler.py

离线评估
python rec/eval/eval.py

生成刷新A/B测试配置
python scripts/prepare_ab_test.py

验证检查分组
python check_group.py

启动数据分析脚本
python analyze_experiment.py

验证路径多样性和BPR模型效果
python test_optimization.py

重启后快速生成测试用户30人
python scripts/init_users.py

重启后补充交互数据样本（脚本）
python batch_feedback.py



启动前后端
后端（Flask）：
python run.py（端口 5000）
前端（Vue）：
npm run dev（端口 5173，已运行）
