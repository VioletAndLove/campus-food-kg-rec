<!-- frontend/src/views/AboutView.vue -->
<template>
  <div class="about-container">
    <!-- 项目介绍 -->
    <el-card class="hero-card" shadow="never">
      <div class="hero-content">
        <div class="project-icon">
          <el-icon :size="80" color="#409eff"><Connection /></el-icon>
        </div>
        <h1 class="project-title">基于知识图谱的校园美食推荐系统</h1>
        <p class="project-subtitle">可解释的智能推荐 · 个性化的美食发现</p>
        <div class="tech-badges">
          <el-tag effect="dark" type="primary">Neo4j</el-tag>
          <el-tag effect="dark" type="success">Flask</el-tag>
          <el-tag effect="dark" type="warning">Vue3</el-tag>
          <el-tag effect="dark" type="danger">PyTorch</el-tag>
        </div>
      </div>
    </el-card>

    <!-- 系统架构 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="section-header">
          <el-icon><SetUp /></el-icon>
          <span>系统架构</span>
        </div>
      </template>

      <div class="architecture-diagram">
        <div class="layer data-layer">
          <div class="layer-title">数据层</div>
          <div class="layer-items">
            <div class="arch-item">Neo4j 图数据库</div>
            <div class="arch-item">菜品知识图谱</div>
            <div class="arch-item">用户交互数据</div>
          </div>
        </div>
        <div class="arrow">↓</div>
        <div class="layer algo-layer">
          <div class="layer-title">算法层</div>
          <div class="layer-items">
            <div class="arch-item">UCPR 路径推理</div>
            <div class="arch-item">TransE 知识嵌入</div>
            <div class="arch-item">BPR 排序优化</div>
          </div>
        </div>
        <div class="arrow">↓</div>
        <div class="layer service-layer">
          <div class="layer-title">服务层</div>
          <div class="layer-items">
            <div class="arch-item">Flask RESTful API</div>
            <div class="arch-item">JWT 认证</div>
            <div class="arch-item">Redis 缓存</div>
          </div>
        </div>
        <div class="arrow">↓</div>
        <div class="layer frontend-layer">
          <div class="layer-title">前端层</div>
          <div class="layer-items">
            <div class="arch-item">Vue3 响应式界面</div>
            <div class="arch-item">Element Plus 组件</div>
            <div class="arch-item">路径可视化</div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 核心特性 -->
    <el-row :gutter="16" class="features-row">
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" shadow="hover">
          <div class="feature-icon" style="background: #e6f7ff;">
            <el-icon color="#1890ff" :size="32"><Share /></el-icon>
          </div>
          <h3>知识图谱驱动</h3>
          <p>基于 Neo4j 构建校园美食知识图谱，融合菜品、口味、食材等多维信息，实现语义化的推荐推理。</p>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" shadow="hover">
          <div class="feature-icon" style="background: #f6ffed;">
            <el-icon color="#52c41a" :size="32"><View /></el-icon>
          </div>
          <h3>可解释推荐</h3>
          <p>不仅告诉用户"推荐什么"，更解释"为什么推荐"，通过可视化路径展示推荐推理过程。</p>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" shadow="hover">
          <div class="feature-icon" style="background: #fff7e6;">
            <el-icon color="#fa8c16" :size="32"><TrendCharts /></el-icon>
          </div>
          <h3>A/B 测试验证</h3>
          <p>内置实验框架，对比可解释推荐与传统推荐的效果，用数据验证解释信息对用户满意度的提升。</p>
        </el-card>
      </el-col>
    </el-row>

    <!-- 算法说明 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="section-header">
          <el-icon><Cpu /></el-icon>
          <span>核心算法：UCPR</span>
        </div>
      </template>

      <div class="algo-content">
        <p class="algo-intro">
          <strong>UCPR（User-Centric Path Reasoning）</strong>是一种以用户为中心的路径推理算法，
          通过采样用户历史菜品与候选菜品之间的多跳路径，实现可解释的个性化推荐。
        </p>

        <el-divider />

        <div class="algo-steps">
          <div class="step-item">
            <div class="step-num">1</div>
            <div class="step-content">
              <h4>路径采样</h4>
              <p>从知识图谱中采样用户历史菜品到候选菜品的 2-3 跳路径，如 Dish→Tag→Dish 或 Dish→Ingredient→Dish。</p>
            </div>
          </div>

          <div class="step-item">
            <div class="step-num">2</div>
            <div class="step-content">
              <h4>嵌入学习</h4>
              <p>使用 TransE 模型学习实体和关系的向量表示，将图谱结构编码为低维稠密向量。</p>
            </div>
          </div>

          <div class="step-item">
            <div class="step-num">3</div>
            <div class="step-content">
              <h4>BPR 优化</h4>
              <p>采用贝叶斯个性化排序（BPR）损失，优化正负样本的区分度，提升推荐准确性。</p>
            </div>
          </div>

          <div class="step-item">
            <div class="step-num">4</div>
            <div class="step-content">
              <h4>多样性评估</h4>
              <p>计算路径多样性指标（Simpson's Index），确保推荐理由的丰富性和覆盖率。</p>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 数据来源 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="section-header">
          <el-icon><DataLine /></el-icon>
          <span>数据规模</span>
        </div>
      </template>

      <el-row :gutter="24" class="stats-row">
        <el-col :span="6">
          <div class="stat-box">
            <div class="stat-number">1,000+</div>
            <div class="stat-label">菜品节点</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-box">
            <div class="stat-number">500</div>
            <div class="stat-label">测试用户</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-box">
            <div class="stat-number">3,000+</div>
            <div class="stat-label">图谱关系</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-box">
            <div class="stat-number">50+</div>
            <div class="stat-label">口味标签</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 项目信息 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="section-header">
          <el-icon><InfoFilled /></el-icon>
          <span>项目信息</span>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="项目名称">基于知识图谱的校园美食推荐系统</el-descriptions-item>
        <el-descriptions-item label="项目代号">UCPR-CampusFood</el-descriptions-item>
        <el-descriptions-item label="技术栈">Neo4j + Flask + Vue3 + PyTorch</el-descriptions-item>
        <el-descriptions-item label="推荐算法">UCPR-BPR (User-Centric Path Reasoning)</el-descriptions-item>
        <el-descriptions-item label="图谱规模">1666 节点，3000+ 关系</el-descriptions-item>
        <el-descriptions-item label="实验设计">A/B 测试（可解释 vs 无解释）</el-descriptions-item>
        <el-descriptions-item label="核心论文" :span="2">
          "Hands on Explainable Recommender Systems with Knowledge Graphs" (RecSys 2022)
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import {
  Connection, SetUp, Share, View, TrendCharts,
  Cpu, DataLine, InfoFilled
} from '@element-plus/icons-vue'
</script>

<style scoped>
.about-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

/* Hero 区域 */
.hero-card {
  margin-bottom: 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.hero-card :deep(.el-card__body) {
  padding: 48px;
}

.hero-content {
  text-align: center;
}

.project-icon {
  margin-bottom: 24px;
}

.project-title {
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 16px 0;
}

.project-subtitle {
  font-size: 18px;
  opacity: 0.9;
  margin: 0 0 24px 0;
}

.tech-badges {
  display: flex;
  justify-content: center;
  gap: 12px;
}

/* 通用卡片 */
.section-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
}

/* 架构图 */
.architecture-diagram {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
}

.layer {
  width: 100%;
  max-width: 600px;
  background: #f5f7fa;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}

.layer-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
  font-weight: 500;
}

.layer-items {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.arch-item {
  background: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  color: #606266;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.arrow {
  font-size: 20px;
  color: #c0c4cc;
  font-weight: bold;
}

.data-layer .arch-item { border-left: 3px solid #409eff; }
.algo-layer .arch-item { border-left: 3px solid #67c23a; }
.service-layer .arch-item { border-left: 3px solid #e6a23c; }
.frontend-layer .arch-item { border-left: 3px solid #f56c6c; }

/* 特性卡片 */
.features-row {
  margin-bottom: 24px;
}

.feature-card {
  height: 100%;
  border-radius: 12px;
  text-align: center;
  padding: 24px;
}

.feature-card :deep(.el-card__body) {
  padding: 0;
}

.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.feature-card h3 {
  font-size: 18px;
  color: #303133;
  margin: 0 0 12px 0;
}

.feature-card p {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

/* 算法步骤 */
.algo-content {
  padding: 24px;
}

.algo-intro {
  font-size: 15px;
  line-height: 1.8;
  color: #303133;
  margin: 0 0 24px 0;
}

.algo-steps {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.step-item {
  display: flex;
  gap: 16px;
}

.step-num {
  width: 40px;
  height: 40px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  flex-shrink: 0;
}

.step-content h4 {
  font-size: 16px;
  color: #303133;
  margin: 0 0 8px 0;
}

.step-content p {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

/* 统计 */
.stats-row {
  padding: 24px;
}

.stat-box {
  text-align: center;
  padding: 24px;
  background: #f5f7fa;
  border-radius: 12px;
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

/* 响应式 */
@media (max-width: 768px) {
  .hero-card :deep(.el-card__body) {
    padding: 32px 24px;
  }

  .project-title {
    font-size: 24px;
  }

  .algo-steps {
    grid-template-columns: 1fr;
  }

  .layer-items {
    flex-direction: column;
    align-items: center;
  }
}
</style>
