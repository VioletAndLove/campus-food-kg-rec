<template>
  <div class="history-container">
    <!-- 顶部导航栏 -->
    <nav class="top-nav">
      <div class="nav-brand" @click="$router.push('/')">
        <el-icon :size="28" color="#667eea"><Food /></el-icon>
        <span class="brand-text">校园美食</span>
      </div>
      <div class="nav-links">
        <el-button link @click="$router.push('/')">首页</el-button>
        <el-button link type="primary">历史记录</el-button>
        <el-button link @click="$router.push('/profile')">个人中心</el-button>
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

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Clock /></el-icon>
          我的美食足迹
        </h1>
        <p class="page-subtitle">共 {{ stats.total }} 次用餐记录，平均评分 {{ stats.avg_rating }} 分</p>
      </div>
      <div class="header-stats">
        <div class="stat-card" v-for="(item, index) in quickStats" :key="index">
          <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
          <div class="stat-label">{{ item.label }}</div>
        </div>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="toolbar">
      <div class="filter-group">
        <el-radio-group v-model="filterType" size="large" @change="handleFilterChange">
          <el-radio-button label="all">全部记录</el-radio-button>
          <el-radio-button label="high">高分好评 (4-5星)</el-radio-button>
          <el-radio-button label="recent">最近一周</el-radio-button>
        </el-radio-group>
      </div>

      <div class="sort-group">
        <el-select v-model="sortBy" size="large" @change="loadHistory">
          <el-option label="最近用餐" value="time_desc" />
          <el-option label="评分最高" value="rating_desc" />
          <el-option label="价格最低" value="price_asc" />
        </el-select>

        <el-input
          v-model="searchKeyword"
          placeholder="搜索菜品..."
          size="large"
          clearable
          style="width: 200px"
          @keyup.enter="loadHistory"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 时间轴视图 -->
    <div class="timeline-view" v-loading="loading">
      <el-timeline v-if="groupedHistory.length > 0">
        <el-timeline-item
          v-for="group in groupedHistory"
          :key="group.date"
          :timestamp="group.date"
          placement="top"
          :type="group.isToday ? 'primary' : 'default'"
        >
          <div class="day-records">
            <div
              v-for="item in group.items"
              :key="item.dish_id"
              class="record-card"
              @click="goToDetail(item.dish_id)"
            >
              <div class="record-image">
                <img v-if="item.photo" :src="getImageUrl(item.photo)" />
                <div v-else class="image-placeholder">
                  <el-icon><Food /></el-icon>
                </div>
                <div class="price-tag">¥{{ item.price }}</div>
              </div>

              <div class="record-info">
                <h3 class="dish-name">{{ item.dish_name }}</h3>
                <div class="record-meta">
                  <el-rate
                    :model-value="item.rating"
                    disabled
                    size="small"
                    show-score
                  />
                  <span class="record-time">{{ formatTime(item.timestamp) }}</span>
                </div>
                <div class="record-tags" v-if="item.tags?.length">
                  <el-tag
                    v-for="tag in item.tags.slice(0, 3)"
                    :key="tag"
                    size="small"
                    effect="plain"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
              </div>

              <div class="record-actions">
                <el-button
                  type="primary"
                  link
                  :icon="View"
                  @click.stop="goToDetail(item.dish_id)"
                >
                  查看
                </el-button>
                <el-popconfirm
                  title="确定删除这条记录？"
                  confirm-button-text="删除"
                  cancel-button-text="取消"
                  @confirm.stop="deleteItem(item.dish_id)"
                >
                  <template #reference>
                    <el-button type="danger" link :icon="Delete" @click.stop>
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>

      <!-- 空状态 -->
      <el-empty
        v-else
        description="暂无用餐记录"
        :image-size="200"
      >
        <el-button type="primary" @click="$router.push('/')">去发现美食</el-button>
      </el-empty>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadHistory"
        @current-change="loadHistory"
      />
    </div>

    <!-- 数据洞察卡片 -->
    <div class="insights-section" v-if="historyItems.length > 5">
      <h2 class="section-title">用餐洞察</h2>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8">
          <div class="insight-card">
            <div class="insight-header">
              <el-icon color="#f56c6c"><TrendCharts /></el-icon>
              <span>口味偏好</span>
            </div>
            <div class="insight-content">
              <div
                v-for="tag in topTags"
                :key="tag.name"
                class="preference-item"
              >
                <span class="pref-name">{{ tag.name }}</span>
                <el-progress
                  :percentage="tag.percentage"
                  :color="tag.color"
                  :show-text="false"
                  class="pref-bar"
                />
                <span class="pref-count">{{ tag.count }}次</span>
              </div>
            </div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <div class="insight-card">
            <div class="insight-header">
              <el-icon color="#e6a23c"><Wallet /></el-icon>
              <span>消费分析</span>
            </div>
            <div class="insight-content center">
              <div class="spending-stat">
                <div class="big-number">¥{{ avgSpending }}</div>
                <div class="stat-desc">平均消费</div>
              </div>
              <div class="spending-range">
                <div class="range-item">
                  <span>最低</span>
                  <strong>¥{{ minPrice }}</strong>
                </div>
                <div class="range-item">
                  <span>最高</span>
                  <strong>¥{{ maxPrice }}</strong>
                </div>
              </div>
            </div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <div class="insight-card">
            <div class="insight-header">
              <el-icon color="#67c23a"><Star /></el-icon>
              <span>评分习惯</span>
            </div>
            <div class="insight-content center">
              <div class="rating-circle">
                <el-progress
                  type="dashboard"
                  :percentage="stats.avg_rating * 20"
                  :color="ratingColor"
                  :stroke-width="10"
                />
                <div class="rating-text">{{ stats.avg_rating }}分</div>
              </div>
              <p class="rating-desc">{{ ratingDesc }}</p>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  Food, UserFilled, ArrowDown, Clock, Search, View, Delete,
  TrendCharts, Wallet, Star
} from '@element-plus/icons-vue'

const router = useRouter()
const { authState, logout } = inject('auth')

const loading = ref(false)
const historyItems = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const sortBy = ref('time_desc')
const searchKeyword = ref('')
const filterType = ref('all')

const stats = ref({
  total: 0,
  avg_rating: 0
})

// 快速统计数据
const quickStats = computed(() => [
  {
    value: stats.value.total,
    label: '总记录',
    color: '#667eea'
  },
  {
    value: historyItems.value.filter(i => i.rating >= 4).length,
    label: '好评数',
    color: '#67c23a'
  },
  {
    value: '¥' + avgSpending.value,
    label: '平均消费',
    color: '#e6a23c'
  }
])

// 计算平均消费
const avgSpending = computed(() => {
  if (historyItems.value.length === 0) return 0
  const sum = historyItems.value.reduce((acc, item) => acc + (item.price || 0), 0)
  return Math.round(sum / historyItems.value.length)
})

const minPrice = computed(() => {
  if (historyItems.value.length === 0) return 0
  return Math.min(...historyItems.value.map(i => i.price || 0))
})

const maxPrice = computed(() => {
  if (historyItems.value.length === 0) return 0
  return Math.max(...historyItems.value.map(i => i.price || 0))
})

// 口味偏好分析
const topTags = computed(() => {
  const tagCount = {}
  historyItems.value.forEach(item => {
    if (item.rating >= 4) {
      item.tags?.forEach(tag => {
        tagCount[tag] = (tagCount[tag] || 0) + 1
      })
    }
  })

  const sorted = Object.entries(tagCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)

  const colors = ['#f56c6c', '#e6a23c', '#67c23a', '#409eff']
  const max = sorted[0]?.[1] || 1

  return sorted.map(([name, count], idx) => ({
    name,
    count,
    percentage: Math.round((count / max) * 100),
    color: colors[idx % colors.length]
  }))
})

const ratingColor = computed(() => {
  const score = stats.value.avg_rating
  if (score >= 4.5) return '#67c23a'
  if (score >= 4) return '#95d475'
  if (score >= 3) return '#e6a23c'
  return '#f56c6c'
})

const ratingDesc = computed(() => {
  const score = stats.value.avg_rating
  if (score >= 4.5) return '您是个美食家！'
  if (score >= 4) return '品味不错哦~'
  if (score >= 3) return '还在探索中'
  return '比较挑剔呢'
})

// 按日期分组
const groupedHistory = computed(() => {
  const groups = {}
  const today = new Date().toDateString()

  historyItems.value.forEach(item => {
    const date = new Date(item.timestamp)
    const dateKey = date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'short'
    })

    if (!groups[dateKey]) {
      groups[dateKey] = {
        date: dateKey,
        isToday: date.toDateString() === today,
        items: []
      }
    }
    groups[dateKey].items.push(item)
  })

  return Object.values(groups).sort((a, b) => {
    return new Date(b.items[0].timestamp) - new Date(a.items[0].timestamp)
  })
})

const getImageUrl = (photo) => {
  if (!photo) return ''
  if (photo.startsWith('http')) return photo
  return `/static/photos/${photo}`
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleFilterChange = () => {
  currentPage.value = 1
  loadHistory()
}

const loadHistory = async () => {
  loading.value = true
  try {
    let minRating = 0
    if (filterType.value === 'high') minRating = 4

    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      sort_by: sortBy.value,
      min_rating: minRating
    }

    const res = await axios.get('/api/v1/history/', {
      params,
      withCredentials: true
    })

    let items = res.data.items || []

    // 客户端关键词过滤
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      items = items.filter(item =>
        item.dish_name.toLowerCase().includes(kw) ||
        item.tags?.some(t => t.toLowerCase().includes(kw))
      )
    }

    historyItems.value = items
    total.value = res.data.total
    stats.value.total = res.data.total

    // 计算平均评分
    if (items.length > 0) {
      const avg = items.reduce((sum, i) => sum + (i.rating || 0), 0) / items.length
      stats.value.avg_rating = avg.toFixed(1)
    }

  } catch (err) {
    console.error('加载历史记录失败:', err)
    ElMessage.error(err.response?.data?.msg || '加载失败')
  } finally {
    loading.value = false
  }
}

// 修复跳转问题 - 添加详细调试
const goToDetail = (dishId) => {
  console.log('[History] 准备跳转到菜品详情:', dishId, '类型:', typeof dishId)

  if (dishId === undefined || dishId === null || dishId === '') {
    console.error('[History] 无效的dishId:', dishId)
    ElMessage.error('无法跳转：无效的菜品ID')
    return
  }

  // 确保是数字
  const id = parseInt(dishId)
  if (isNaN(id)) {
    console.error('[History] dishId不是有效数字:', dishId)
    ElMessage.error('无法跳转：菜品ID格式错误')
    return
  }

  console.log('[History] 执行跳转: /dish/' + id)
  router.push(`/dish/${id}`)
}

const deleteItem = async (dishId) => {
  try {
    await axios.delete(`/api/v1/history/${dishId}`, {
      withCredentials: true
    })
    ElMessage.success('已删除')
    loadHistory()
  } catch (err) {
    ElMessage.error(err.response?.data?.msg || '删除失败')
  }
}

const handleCommand = (cmd) => {
  switch (cmd) {
    case 'profile':
      router.push('/profile')
      break
    case 'history':
      router.push('/history')
      break
    case 'logout':
      logout()
      ElMessage.success('已退出登录')
      router.push('/login')
      break
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
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

/* 页面头部 */
.history-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  min-height: 100vh;
  background: #f8fafc;
  padding-top: 88px; /* 为导航栏留出空间 */
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 32px;
  color: #fff;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 24px;
}

.stat-card {
  text-align: center;
  background: rgba(255,255,255,0.15);
  padding: 16px 24px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  opacity: 0.9;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

.sort-group {
  display: flex;
  gap: 12px;
}

/* 时间轴视图 */
.timeline-view {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
  min-height: 400px;
}

:deep(.el-timeline-item__node) {
  width: 14px;
  height: 14px;
}

:deep(.el-timeline-item__timestamp) {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.day-records {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.record-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.3s ease;
}

.record-card:hover {
  background: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.record-image {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
  background: #f3f4f6;
}

.record-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.price-tag {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0,0,0,0.6);
  color: #fff;
  text-align: center;
  padding: 4px;
  font-size: 12px;
  font-weight: 600;
}

.record-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dish-name {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.record-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.record-time {
  font-size: 13px;
  color: #9ca3af;
}

.record-tags {
  display: flex;
  gap: 8px;
}

.record-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 40px;
}

/* 洞察区域 */
.insights-section {
  margin-top: 40px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 20px;
}

.insight-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  height: 100%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.insight-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f3f4f6;
}

.insight-content {
  min-height: 150px;
}

.insight-content.center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.preference-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.pref-name {
  width: 60px;
  font-size: 14px;
  color: #4b5563;
}

.pref-bar {
  flex: 1;
}

.pref-count {
  width: 50px;
  text-align: right;
  font-size: 13px;
  color: #9ca3af;
}

.spending-stat {
  text-align: center;
  margin-bottom: 20px;
}

.big-number {
  font-size: 42px;
  font-weight: 700;
  color: #667eea;
  line-height: 1;
}

.stat-desc {
  font-size: 14px;
  color: #6b7280;
  margin-top: 8px;
}

.spending-range {
  display: flex;
  gap: 40px;
}

.range-item {
  text-align: center;
}

.range-item span {
  display: block;
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 4px;
}

.range-item strong {
  font-size: 18px;
  color: #1a1a2e;
}

.rating-circle {
  position:relative;
  margin-bottom: 16px;
}

.rating-text {
  position:absolute;
  top: 80%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
}

.rating-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .top-nav {
    padding: 0 20px;
  }

  .nav-links {
    display: none;
  }

  .page-header {
    flex-direction: column;
    text-align: center;
    gap: 24px;
  }

  .header-stats {
    width: 100%;
    justify-content: center;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .sort-group {
    flex-direction: column;
  }

  .record-card {
    flex-direction: column;
  }

  .record-image {
    width: 100%;
    height: 200px;
  }

  .history-container {
    padding-top: 80px;
  }
}
</style>
