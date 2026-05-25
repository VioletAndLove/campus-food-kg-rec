<template>
  <div class="profile-container">
    <nav class="top-nav">
      <div class="nav-brand" @click="$router.push('/')">
        <el-icon :size="28" color="#667eea"><Food /></el-icon>
        <span class="brand-text">校园美食</span>
      </div>
      <div class="nav-links">
        <el-button link @click="$router.push('/')">首页</el-button>
        <el-button link @click="$router.push('/history')">历史记录</el-button>
        <el-button link type="primary">个人中心</el-button>
      </div>
      <div class="nav-user">
        <template v-if="authState.is_logged_in">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :icon="UserFilled" />
              <span class="username">{{ authState.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="history">历史记录</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" @click="$router.push('/login')">登录</el-button>
        </template>
      </div>
    </nav>

    <!-- 头部用户信息卡片 -->
    <div class="profile-header">
      <div class="header-bg"></div>
      <div class="header-content">
        <div class="avatar-section">
          <el-avatar :size="100" :icon="UserFilled" class="user-avatar" />
          <div class="user-badge" :class="experimentClass">
            {{ profile.experiment_group }}
          </div>
        </div>

        <div class="user-main">
          <h1 class="username2">{{ profile.username }}</h1>
          <p class="user-id">ID: {{ profile.user_id }}</p>
          <p class="join-date" v-if="profile.created_at !== '未知'">
            <el-icon><Calendar /></el-icon>
            注册于 {{ formatDate(profile.created_at) }}
          </p>
        </div>

        <div class="user-stats">
          <div class="stat-item">
            <div class="stat-number">{{ profile.total_interactions }}</div>
            <div class="stat-label">用餐记录</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-number" :style="{ color: ratingColor }">
              {{ profile.avg_rating }}
            </div>
            <div class="stat-label">平均评分</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-number">{{ profile.favorite_tags?.length || 0 }}</div>
            <div class="stat-label">偏好口味</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="profile-content">
      <!-- 左侧：口味画像 -->
      <div class="content-left">
        <!-- 口味偏好词云 -->
        <el-card class="preference-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="header-title">
                <el-icon><IceCream /></el-icon>
                我的口味画像
              </span>
              <el-tag type="info" size="small">基于历史记录分析</el-tag>
            </div>
          </template>

          <div v-if="profile.favorite_tags?.length > 0" class="tag-cloud">
            <div
              v-for="(tag, index) in profile.favorite_tags"
              :key="tag.tag"
              class="cloud-tag"
              :style="getTagStyle(index, tag.count)"
            >
              {{ tag.tag }}
              <span class="tag-count">{{ tag.count }}次</span>
            </div>
          </div>

          <el-empty v-else description="还没有足够的用餐数据" :image-size="100" />
        </el-card>

        <!-- 偏好食材 -->
        <el-card class="preference-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="header-title">
                <el-icon><Food /></el-icon>
                偏好的食材
              </span>
            </div>
          </template>

          <div v-if="profile.favorite_ingredients?.length > 0" class="ingredient-list">
            <div
              v-for="item in profile.favorite_ingredients"
              :key="item.ingredient"
              class="ingredient-item"
            >
              <div class="ingredient-icon">
                <el-icon><CircleCheckFilled /></el-icon>
              </div>
              <div class="ingredient-info">
                <span class="ingredient-name">{{ item.ingredient }}</span>
                <el-progress
                  :percentage="Math.min(item.count * 10, 100)"
                  :color="getIngredientColor(item.count)"
                  :show-text="false"
                  class="ingredient-bar"
                />
              </div>
              <el-tag size="small" type="success" effect="light">
                {{ item.count }}次
              </el-tag>
            </div>
          </div>

          <el-empty v-else description="探索更多菜品来发现偏好" :image-size="100" />
        </el-card>

        <!-- 实验分组信息 -->
        <el-card class="experiment-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="header-title">
                <el-icon><InfoFilled /></el-icon>
                实验参与情况
              </span>
            </div>
          </template>

          <div class="experiment-info">
            <div class="info-row">
              <span class="info-label">当前分组</span>
              <el-tag :type="experimentTagType" size="large" effect="dark">
                {{ profile.experiment_group }}
              </el-tag>
            </div>
            <div class="info-row">
              <span class="info-label">推荐模式</span>
              <span class="info-value">
                {{ profile.show_explanation ? '显示推理路径（可解释推荐）' : '隐藏推理路径（传统推荐）' }}
              </span>
            </div>
            <div class="info-desc">
              <el-alert
                :title="experimentDesc"
                :type="profile.show_explanation ? 'success' : 'info'"
                :closable="false"
                show-icon
              />
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧：数据分析与操作 -->
      <div class="content-right">
        <!-- 用餐趋势图 -->
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="header-title">
                <el-icon><TrendCharts /></el-icon>
                用餐趋势
              </span>
              <el-radio-group v-model="trendPeriod" size="small">
                <el-radio-button label="week">近7天</el-radio-button>
                <el-radio-button label="month">近30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>

          <div class="trend-chart" ref="chartRef">
            <!-- 简化的趋势展示 -->
            <div class="trend-bars">
              <div
                v-for="(day, idx) in trendData"
                :key="idx"
                class="trend-day"
              >
                <div
                  class="trend-bar"
                  :style="{ height: day.count * 20 + 'px', opacity: 0.3 + day.count * 0.2 }"
                ></div>
                <span class="trend-label">{{ day.label }}</span>
                <span class="trend-count">{{ day.count }}次</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 评分分布 -->
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="header-title">
                <el-icon><StarFilled /></el-icon>
                评分分布
              </span>
            </div>
          </template>

          <div class="rating-distribution">
            <div v-for="i in 5" :key="i" class="dist-row">
              <span class="star-num">{{ 6-i }}星</span>
              <el-progress
                :percentage="getRatingPercentage(6-i)"
                :color="getStarColor(6-i)"
                class="dist-bar"
              />
              <span class="dist-count">{{ getRatingCount(6-i) }}</span>
            </div>
          </div>
        </el-card>

        <!-- 快捷操作 -->
        <el-card class="action-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="header-title">
                <el-icon><Setting /></el-icon>
                账号管理
              </span>
            </div>
          </template>

          <div class="action-list">
            <el-button class="action-btn" @click="refreshData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              <div class="btn-content">
                <span class="btn-title">刷新数据</span>
                <span class="btn-desc">同步最新用餐记录</span>
              </div>
            </el-button>

            <el-button class="action-btn" @click="goToHistory">
              <el-icon><Clock /></el-icon>
              <div class="btn-content">
                <span class="btn-title">查看历史</span>
                <span class="btn-desc">浏览全部用餐记录</span>
              </div>
            </el-button>

            <el-divider />

            <el-button class="action-btn danger" @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>
              <div class="btn-content">
                <span class="btn-title">退出登录</span>
                <span class="btn-desc">清除当前会话</span>
              </div>
            </el-button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UserFilled, Calendar, IceCream, Food, CircleCheckFilled,
  InfoFilled, TrendCharts, StarFilled, Setting,
  Refresh, Clock, SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const { authState, logout, updateAuthState } = inject('auth')

const loading = ref(false)
const trendPeriod = ref('week')
const profile = ref({
  user_id: 0,
  username: '',
  created_at: '',
  total_interactions: 0,
  avg_rating: 0,
  favorite_tags: [],
  favorite_ingredients: [],
  experiment_group: '未分组',
  show_explanation: false
})

// 模拟趋势数据（实际应从后端获取）
const trendData = ref([
  { label: '周一', count: 2 },
  { label: '周二', count: 1 },
  { label: '周三', count: 3 },
  { label: '周四', count: 0 },
  { label: '周五', count: 2 },
  { label: '周六', count: 4 },
  { label: '周日', count: 3 }
])

// 计算属性
const experimentClass = computed(() => {
  const group = profile.value.experiment_group
  if (group?.includes('A')) return 'group-a'
  if (group?.includes('B')) return 'group-b'
  return 'group-unknown'
})

const experimentTagType = computed(() => {
  const group = profile.value.experiment_group
  if (group?.includes('A')) return 'success'
  if (group?.includes('B')) return 'warning'
  return 'info'
})

const experimentDesc = computed(() => {
  if (profile.value.show_explanation) {
    return '您当前使用的是"可解释推荐"版本，可以看到系统为什么推荐这些菜品'
  }
  return '您当前使用的是"传统推荐"版本，系统直接展示推荐结果'
})

const ratingColor = computed(() => {
  const score = profile.value.avg_rating
  if (score >= 4.5) return '#67c23a'
  if (score >= 4) return '#95d475'
  if (score >= 3) return '#e6a23c'
  return '#f56c6c'
})

// 方法
const formatDate = (dateStr) => {
  if (!dateStr || dateStr === '未知') return '未知'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const getTagStyle = (index, count) => {
  const sizes = ['32px', '26px', '22px', '18px', '16px']
  const colors = ['#667eea', '#764ba2', '#f56c6c', '#e6a23c', '#67c23a']
  return {
    fontSize: sizes[index] || '14px',
    color: colors[index % colors.length],
    opacity: 1 - index * 0.15
  }
}

const getIngredientColor = (count) => {
  if (count >= 5) return '#67c23a'
  if (count >= 3) return '#e6a23c'
  return '#909399'
}

const getStarColor = (star) => {
  const colors = {
    5: '#67c23a',
    4: '#95d475',
    3: '#e6a23c',
    2: '#f89898',
    1: '#f56c6c'
  }
  return colors[star] || '#909399'
}

const getRatingPercentage = (star) => {
  // 模拟数据，实际应从后端获取分布
  const dist = { 5: 45, 4: 30, 3: 15, 2: 7, 1: 3 }
  return dist[star] || 0
}

const getRatingCount = (star) => {
  const total = profile.value.total_interactions
  return Math.round(total * getRatingPercentage(star) / 100)
}

const loadProfile = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/profile/', {
      withCredentials: true
    })
    profile.value = res.data

    // 更新全局状态
    updateAuthState({
      user_id: res.data.user_id,
      username: res.data.username
    })
  } catch (err) {
    console.error('加载个人中心失败:', err)
    if (err.response?.status === 401) {
      ElMessage.error('请先登录')
      router.push('/login')
    } else {
      ElMessage.error(err.response?.data?.msg || '加载失败')
    }
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadProfile()
  ElMessage.success('数据已刷新')
}

const goToHistory = () => {
  router.push('/history')
}

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await logout()
    router.push('/login')
    ElMessage.success('已退出登录')
  }).catch(() => {})
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  min-height: 100vh;
  background: #f8fafc;
}

/* 导航栏样式 */
.top-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  z-index: 100;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-text {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
}

.nav-links {
  display: flex;
  gap: 8px;
}

.nav-user {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 20px;
  transition: background 0.3s;
}

.user-info:hover {
  background: #f3f4f6;
}

.username {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

/* 头部区域 */
.profile-header {
  position: relative;
  margin-bottom: 24px;
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.header-bg {
  height: 120px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header-content {
  position: relative;
  padding: 0 32px 32px;
  display: flex;
  align-items: flex-end;
  gap: 24px;
  margin-top: -50px;
}

.avatar-section {
  position: relative;
  flex-shrink: 0;
}

.user-avatar {
  border: 4px solid #fff;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.user-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  border: 2px solid #fff;
}

.group-a {
  background: #67c23a;
}

.group-b {
  background: #e6a23c;
}

.group-unknown {
  background: #909399;
}

.user-main {
  flex: 1;
  padding-bottom: 8px;
}

.username2 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px 0;
}

.user-id {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 4px 0;
}

.join-date {
  font-size: 13px;
  color: #9ca3af;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-stats {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 16px 24px;
  background: #f9fafb;
  border-radius: 16px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #667eea;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: #e5e7eb;
}

/* 主内容区 */
.profile-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.content-left,
.content-right {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 卡片样式 */
:deep(.el-card) {
  border-radius: 16px;
  border: none;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

:deep(.el-card__header) {
  border-bottom: 1px solid #f3f4f6;
  padding: 20px 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 口味词云 */
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 20px;
  align-items: baseline;
  justify-content: center;
  min-height: 200px;
}

.cloud-tag {
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: default;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.cloud-tag:hover {
  transform: scale(1.1);
}

.tag-count {
  font-size: 12px;
  font-weight: normal;
  opacity: 0.7;
}

/* 食材列表 */
.ingredient-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px;
}

.ingredient-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.ingredient-item:hover {
  background: #f3f4f6;
}

.ingredient-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #dcfce7;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #22c55e;
  font-size: 20px;
}

.ingredient-info {
  flex: 1;
}

.ingredient-name {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.ingredient-bar {
  margin: 0;
}

/* 实验信息 */
.experiment-info {
  padding: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
}

.info-label {
  width: 80px;
  font-size: 14px;
  color: #6b7280;
  flex-shrink: 0;
}

.info-value {
  flex: 1;
  font-size: 14px;
  color: #1a1a2e;
}

.info-desc {
  margin-top: 20px;
}

/* 趋势图 */
.trend-chart {
  padding: 20px;
  height: 200px;
}

.trend-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 100%;
  gap: 16px;
}

.trend-day {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.trend-bar {
  width: 100%;
  background: linear-gradient(to top, #667eea, #764ba2);
  border-radius: 6px 6px 0 0;
  transition: all 0.3s ease;
  min-height: 4px;
}

.trend-bar:hover {
  opacity: 0.8;
  transform: scaleY(1.05);
}

.trend-label {
  font-size: 12px;
  color: #6b7280;
}

.trend-count {
  font-size: 11px;
  color: #9ca3af;
}

/* 评分分布 */
.rating-distribution {
  padding: 20px;
}

.dist-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.star-num {
  width: 40px;
  font-size: 13px;
  color: #6b7280;
}

.dist-bar {
  flex: 1;
}

.dist-count {
  width: 40px;
  text-align: right;
  font-size: 13px;
  color: #9ca3af;
}

/* 操作列表 */
.action-list {
  padding: 8px;
}

.action-btn {
  width: 100%;
  height: auto;
  padding: 16px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-radius: 12px;
  justify-content: flex-start;
}

.action-btn .el-icon {
  font-size: 24px;
  color: #667eea;
}

.btn-content {
  text-align: left;
}

.btn-title {
  display: block;
  font-size: 15px;
  font-weight: 500;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.btn-desc {
  font-size: 12px;
  color: #9ca3af;
}

.action-btn.danger .el-icon {
  color: #f56c6c;
}

.action-btn.danger .btn-title {
  color: #f56c6c;
}

/* 响应式 */
@media (max-width: 1024px) {
  .top-nav {
    padding: 0 20px;
  }

  .profile-content {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding-top: 20px;
  }

  .user-stats {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 640px) {
  .top-nav {
    padding: 0 20px;
  }

  .nav-links {
    display: none;
  }

  .user-stats {
    flex-direction: column;
    gap: 16px;
  }

  .stat-divider {
    display: none;
  }
}
</style>
