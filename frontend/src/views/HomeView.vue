<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <nav class="top-nav">
      <div class="nav-brand" @click="$router.push('/')">
        <el-icon :size="28" color="#667eea"><Food /></el-icon>
        <span class="brand-text">校园美食</span>
      </div>
      <div class="nav-links">
        <el-button link @click="$router.push('/history')">历史记录</el-button>
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

    <!-- 搜索区域 -->
    <div class="search-section">
      <div class="search-wrapper">
        <h1 class="search-title">发现你的专属美食</h1>
        <p class="search-subtitle">基于知识图谱的智能推荐，让每一餐都有惊喜</p>

        <!-- 搜索框 -->
        <div class="search-box">
          <el-input
            v-model="searchQuery"
            placeholder="搜索菜品名称、食材、口味、学校..."
            size="large"
            class="search-input"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #append>
              <el-button type="primary" @click="handleSearch" :loading="searchLoading">
                搜索
              </el-button>
            </template>
          </el-input>

          <!-- 筛选按钮 -->
          <el-button
            class="filter-btn"
            :type="showFilters ? 'primary' : 'default'"
            @click="showFilters = !showFilters"
          >
            <el-icon><Filter /></el-icon>
            筛选
          </el-button>
        </div>

        <!-- 筛选面板 -->
        <el-collapse-transition>
          <div v-show="showFilters" class="filter-panel">
            <el-card shadow="never" class="filter-card">
              <div class="filter-row">
                <!-- 口味筛选 -->
                <div class="filter-group">
                  <label class="filter-label">口味偏好</label>
                  <el-select-v2
                    v-model="filters.tags"
                    :options="tagOptions"
                    multiple
                    collapse-tags
                    placeholder="选择口味标签"
                    class="filter-select"
                    style="width: 200px"
                  />
                </div>

                <!-- 食材筛选 -->
                <div class="filter-group">
                  <label class="filter-label">食材偏好</label>
                  <el-select-v2
                    v-model="filters.ingredients"
                    :options="ingredientOptions"
                    multiple
                    collapse-tags
                    placeholder="选择食材"
                    class="filter-select"
                    style="width: 200px"
                  />
                </div>

                <!-- 价格区间 -->
                <div class="filter-group">
                  <label class="filter-label">价格区间</label>
                  <el-slider
                    v-model="filters.priceRange"
                    range
                    :min="0"
                    :max="50"
                    :step="5"
                    show-stops
                    class="price-slider"
                  />
                  <div class="price-labels">
                    <span>¥{{ filters.priceRange[0] }}</span>
                    <span>¥{{ filters.priceRange[1] }}</span>
                  </div>
                </div>
              </div>

              <div class="filter-actions">
                <el-button @click="resetFilters">重置</el-button>
                <el-button type="primary" @click="applyFilters">应用筛选</el-button>
              </div>
            </el-card>
          </div>
        </el-collapse-transition>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 搜索结果区（优先显示） -->
      <div v-if="searchResults.length > 0" class="content-section">
        <div class="section-header">
          <h2 class="section-title">
            <el-icon><Search /></el-icon>
            搜索结果 ({{ searchResults.length }})
          </h2>
          <el-button link @click="clearSearch">清除搜索</el-button>
        </div>

        <el-row :gutter="20">
          <el-col
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
            v-for="item in searchResults"
            :key="'search-'+item.dish_id"
          >
            <dish-card :dish="item" @click="goToDetail(item.dish_id)" />
          </el-col>
        </el-row>
      </div>

      <!-- 推荐结果区 -->
      <div class="content-section">
        <div class="section-header">
          <h2 class="section-title">
            <el-icon><StarFilled /></el-icon>
            为你推荐
            <el-tag v-if="fromCache" type="info" size="small" effect="plain">来自缓存</el-tag>
          </h2>
          <div class="section-actions">
            <el-radio-group v-model="topk" size="small" @change="refreshRecommendations">
              <el-radio-button :value="5">5个</el-radio-button>
              <el-radio-button :value="10">10个</el-radio-button>
              <el-radio-button :value="20">20个</el-radio-button>
            </el-radio-group>
            <el-button
              :icon="Refresh"
              circle
              size="small"
              @click="refreshRecommendations(true)"
              :loading="loading"
            />
          </div>
        </div>

        <!-- 未登录提示 -->
        <el-alert
          v-if="!authState.is_logged_in"
          title="登录后可获取个性化推荐"
          type="info"
          show-icon
          :closable="false"
          class="login-tip"
        >
          <el-button type="primary" size="small" @click="$router.push('/login')">立即登录</el-button>
        </el-alert>

        <!-- 推荐列表 -->
        <el-skeleton :rows="3" animated v-if="loading && recommendations.length === 0" />

        <el-empty
          v-else-if="!loading && recommendations.length === 0 && authState.is_logged_in"
          description="暂无推荐数据"
        />

        <el-row :gutter="20" v-else>
          <el-col
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
            v-for="item in recommendations"
            :key="'rec-'+item.dish_id"
          >
            <dish-card
              :dish="item"
              :is-recommendation="true"
              @click="goToDetail(item.dish_id)"
            />
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, inject, onMounted, onActivated } from 'vue'

defineOptions({ name: 'Home' })
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  Food, UserFilled, ArrowDown, Search, Filter,
  StarFilled, Refresh
} from '@element-plus/icons-vue'
import DishCard from '../components/DishCard.vue'

const router = useRouter()
const { authState, logout, checkAuthStatus } = inject('auth')

// 搜索相关
const searchQuery = ref('')
const searchResults = ref([])
const searchLoading = ref(false)
const showFilters = ref(false)

// 筛选条件
const filters = ref({
  tags: [],
  ingredients: [],
  priceRange: [0, 50]
})

// 从数据库加载的选项
const tagOptions = ref([])
const ingredientOptions = ref([])

// 推荐相关
const topk = ref(10)
const loading = ref(false)
const recommendations = ref([])
const fromCache = ref(false)

// 缓存键
const CACHE_KEY = 'home_recommendations'
const CACHE_TIME_KEY = 'home_cache_time'
const CACHE_DURATION = 30 * 60 * 1000 // 30分钟

// 加载筛选选项
const loadFilterOptions = async () => {
  try {
    const res = await axios.get('/api/v1/dish/filters', {
      withCredentials: true
    })
    tagOptions.value = (res.data.tags || []).map(t => ({ label: t, value: t }))
    ingredientOptions.value = (res.data.ingredients || []).map(i => ({ label: i, value: i }))
  } catch (err) {
    console.error('加载筛选选项失败:', err)
    // 使用默认值
    tagOptions.value = [
      { label: '辣', value: '辣' },
      { label: '清淡', value: '清淡' },
      { label: '酸甜', value: '酸甜' },
      { label: '咸鲜', value: '咸鲜' },
      { label: '麻辣', value: '麻辣' }
    ]
    ingredientOptions.value = [
      { label: '猪肉', value: '猪肉' },
      { label: '牛肉', value: '牛肉' },
      { label: '鸡肉', value: '鸡肉' },
      { label: '豆腐', value: '豆腐' },
      { label: '鸡蛋', value: '鸡蛋' }
    ]
  }
}

// 组件激活时检查缓存
onActivated(() => {
  const cached = loadFromCache()
  if (cached && !isCacheExpired()) {
    recommendations.value = cached
    fromCache.value = true
  } else if (authState.value.is_logged_in && recommendations.value.length === 0) {
    getRecommendations()
  }
})

onMounted(() => {
  checkAuthStatus()
  loadFilterOptions()
  // 尝试从缓存加载
  const cached = loadFromCache()
  if (cached && !isCacheExpired()) {
    recommendations.value = cached
    fromCache.value = true
  } else if (authState.value.is_logged_in) {
    getRecommendations()
  }
})

// 缓存操作
const saveToCache = (data) => {
  localStorage.setItem(CACHE_KEY, JSON.stringify(data))
  localStorage.setItem(CACHE_TIME_KEY, Date.now().toString())
}

const loadFromCache = () => {
  try {
    const cached = localStorage.getItem(CACHE_KEY)
    return cached ? JSON.parse(cached) : null
  } catch {
    return null
  }
}

const isCacheExpired = () => {
  const time = localStorage.getItem(CACHE_TIME_KEY)
  if (!time) return true
  return Date.now() - parseInt(time) > CACHE_DURATION
}

const clearCache = () => {
  localStorage.removeItem(CACHE_KEY)
  localStorage.removeItem(CACHE_TIME_KEY)
}

// 搜索功能（支持模糊查询）
const handleSearch = async () => {
  if (!searchQuery.value.trim() && filters.value.tags.length === 0 && filters.value.ingredients.length === 0) {
    ElMessage.warning('请输入搜索内容或选择筛选条件')
    return
  }

  searchLoading.value = true
  try {
    const res = await axios.post('/api/v1/dish/search', {
      query: searchQuery.value,
      tags: filters.value.tags,
      ingredients: filters.value.ingredients,
      min_price: filters.value.priceRange[0],
      max_price: filters.value.priceRange[1]
    }, {
      withCredentials: true
    })
    searchResults.value = res.data.results || []
    if (searchResults.value.length === 0) {
      ElMessage.info('未找到匹配的菜品')
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.message || '搜索失败')
  } finally {
    searchLoading.value = false
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
}

const resetFilters = () => {
  filters.value = {
    tags: [],
    ingredients: [],
    priceRange: [0, 50]
  }
}

const applyFilters = () => {
  handleSearch()
  showFilters.value = false
}

// 推荐功能
const getRecommendations = async (forceRefresh = false) => {
  if (!authState.value.is_logged_in) return

  // 检查缓存
  if (!forceRefresh) {
    const cached = loadFromCache()
    if (cached && !isCacheExpired()) {
      recommendations.value = cached
      fromCache.value = true
      return
    }
  }

  loading.value = true
  fromCache.value = false

  try {
    const res = await axios.post('/api/v1/rec/', {
      user_id: authState.value.user_id,
      topk: topk.value
    }, {
      withCredentials: true
    })

    recommendations.value = res.data.recommendations || []
    saveToCache(recommendations.value)

  } catch (err) {
    ElMessage.error(err.response?.data?.message || '获取推荐失败')
  } finally {
    loading.value = false
  }
}

const refreshRecommendations = (force = false) => {
  if (force) {
    clearCache()
  }
  getRecommendations(force)
}

// 导航 - 修复跳转问题，添加调试
const goToDetail = (dishId) => {
  console.log('[Home] 准备跳转到菜品详情:', dishId, '类型:', typeof dishId)

  if (dishId === undefined || dishId === null || dishId === '') {
    console.error('[Home] 无效的dishId:', dishId)
    ElMessage.error('无法跳转：无效的菜品ID')
    return
  }

  // 确保是数字
  const id = parseInt(dishId)
  if (isNaN(id)) {
    console.error('[Home] dishId不是有效数字:', dishId)
    ElMessage.error('无法跳转：菜品ID格式错误')
    return
  }

  console.log('[Home] 执行跳转: /dish/' + id)
  router.push(`/dish/${id}`)
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
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #f8fafc;
}

/* 顶部导航 */
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

/* 搜索区域 */
.search-section {
  padding-top: 64px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.search-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding: 60px 20px;
  text-align: center;
  position: relative;
  z-index: 2;
}

.search-title {
  font-size: 42px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 12px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.search-subtitle {
  font-size: 16px;
  color: rgba(255,255,255,0.9);
  margin-bottom: 40px;
}

.search-box {
  display: flex;
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.search-input {
  flex: 1;
}

:deep(.search-input .el-input__wrapper) {
  border-radius: 12px;
  padding: 8px 16px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

:deep(.search-input .el-input__inner) {
  height: 48px;
  font-size: 16px;
}

.filter-btn {
  height: 48px;
  border-radius: 12px;
  padding: 0 20px;
  font-size: 14px;
}

/* 筛选面板 */
.filter-panel {
  max-width: 700px;
  margin: 20px auto 0;
}

.filter-card {
  border-radius: 12px;
}

.filter-row {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.filter-group {
  flex: 1;
  min-width: 180px;
}

.filter-label {
  display: block;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
  font-weight: 500;
}

.filter-select {
  width: 100%;
}

.price-slider {
  margin-top: 8px;
}

.price-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

/* 主内容区 */
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 20px;
}

.content-section {
  margin-bottom: 50px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
}

.section-title .el-tag {
  font-weight: normal;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.login-tip {
  margin-bottom: 20px;
}

/* 响应式 */
@media (max-width: 768px) {
  .top-nav {
    padding: 0 20px;
  }

  .nav-links {
    display: none;
  }

  .search-title {
    font-size: 28px;
  }

  .search-box {
    flex-direction: column;
  }

  .filter-row {
    flex-direction: column;
  }
}
</style>
