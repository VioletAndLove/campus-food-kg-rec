<template>
  <div class="detail-container" v-if="dish">
    <!-- 顶部导航 -->
    <nav class="detail-nav">
      <el-button link @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div class="nav-title">菜品详情</div>
      <div class="nav-actions">
        <el-button :icon="Share" circle text />
        <el-button :icon="Star" circle text @click="toggleFavorite" />
      </div>
    </nav>

    <div class="detail-content">
      <!-- 左侧：菜品信息 -->
      <div class="info-section">
        <!-- 图片区 -->
        <div class="image-gallery">
          <div class="main-image">
            <img v-if="dish.photo" :src="getImageUrl(dish.photo)" :alt="dish.name" />
            <div v-else class="image-placeholder">
              <el-icon :size="80"><Food /></el-icon>
            </div>
            <div class="price-badge">¥{{ dish.price }}</div>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="info-card">
          <h1 class="dish-name">{{ dish.name }}</h1>

          <div class="rating-summary" v-if="dish.total_comments > 0">
            <el-rate
              :model-value="dish.avg_rating"
              disabled
              show-score
              text-color="#ff9900"
            />
            <span class="rating-count">{{ dish.total_comments }}条评价</span>
          </div>

          <div class="tags-section">
            <h4>口味标签</h4>
            <div class="tags-list">
              <el-tag
                v-for="tag in dish.tags"
                :key="tag"
                type="primary"
                effect="light"
                size="large"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>

          <div class="ingredients-section">
            <h4>主要食材</h4>
            <div class="ingredients-list">
              <span
                v-for="ing in dish.ingredients"
                :key="ing"
                class="ingredient-item"
              >
                <el-icon><CircleCheck /></el-icon>
                {{ ing }}
              </span>
            </div>
          </div>

          <!-- 推荐理由 -->
          <div class="explanation-section" v-if="dish.explanation && dish.paths?.length > 0">
            <h4>
              <el-icon><MagicStick /></el-icon>
              推荐理由
            </h4>
            <el-alert :title="dish.explanation" type="success" :closable="false" show-icon />

            <div class="paths-list">
              <div v-for="(path, index) in dish.paths" :key="index" class="path-item">
                <div class="path-header">推理路径 {{ index + 1 }}</div>
                <div class="path-flow">
                  <span class="node start">您</span>
                  <template v-for="(step, idx) in formatPath(path)" :key="idx">
                    <span class="arrow">→</span>
                    <span class="relation">{{ step.relation }}</span>
                    <span class="arrow">→</span>
                    <span class="node" :class="{ end: step.isLast }">{{ step.entity }}</span>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <!-- 智能搭配 -->
          <div class="combo-section" v-if="combo.combo_items?.length > 0">
            <h4>
              <el-icon><Dish /></el-icon>
              智能搭配
            </h4>
            <el-alert :title="combo.explanation" type="warning" :closable="false" show-icon />

            <div class="combo-list">
              <!-- 主菜（当前菜品） -->
              <div class="combo-card main-card">
                <div class="combo-image">
                  <img v-if="combo.main_dish?.photo" :src="getImageUrl(combo.main_dish.photo)" />
                  <div v-else class="combo-placeholder"><el-icon><Food /></el-icon></div>
                </div>
                <div class="combo-info">
                  <div class="combo-name">{{ combo.main_dish?.name }}</div>
                  <div class="combo-price">¥{{ combo.main_dish?.price }}</div>
                  <el-tag size="small" type="success">主菜</el-tag>
                </div>
              </div>

              <div class="combo-plus">+</div>

              <!-- 推荐配菜 -->
              <div
                v-for="item in combo.combo_items"
                :key="item.dish_id"
                class="combo-card"
                @click="goToDetail(item.dish_id)"
              >
                <div class="combo-image">
                  <img v-if="item.photo" :src="getImageUrl(item.photo)" />
                  <div v-else class="combo-placeholder"><el-icon><Food /></el-icon></div>
                </div>
                <div class="combo-info">
                  <div class="combo-name">{{ item.name }}</div>
                  <div class="combo-price">¥{{ item.price }}</div>
                  <el-tag size="small" type="info" effect="light">{{ item.reason }}</el-tag>
                  <div class="combo-meta">
                    <el-rate :model-value="item.avg_rating" disabled size="small" />
                    <span class="combo-co" v-if="item.co_occurrence > 0">{{ item.co_occurrence }}人同选</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="combo-summary">
              <span class="combo-total">
                套餐总价: <strong>¥{{ combo.total_price }}</strong>
              </span>
              <span class="combo-budget" v-if="combo.budget">
                / 预算 ¥{{ combo.budget }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：评论区 -->
      <div class="comments-section">
        <div class="comments-header">
          <h2>
            <el-icon><ChatDotRound /></el-icon>
            用户评价
          </h2>
          <el-button
            v-if="authState.is_logged_in"
            type="primary"
            @click="showCommentDialog = true"
          >
            写评价
          </el-button>
          <el-button v-else @click="$router.push('/login')">登录后评价</el-button>
        </div>

        <!-- 评分分布 -->
        <div class="rating-distribution" v-if="ratingStats.length > 0">
          <div v-for="stat in ratingStats" :key="stat.star" class="rating-bar">
            <span class="star-label">{{ stat.star }}星</span>
            <el-progress
              :percentage="stat.percentage"
              :color="stat.color"
              :show-text="false"
              class="progress-bar"
            />
            <span class="count-label">{{ stat.count }}</span>
          </div>
        </div>

        <!-- 评论列表 -->
        <div class="comments-list" v-loading="commentsLoading">
          <div
            v-for="comment in dish.comments"
            :key="comment.comment_id"
            class="comment-item"
          >
            <div class="comment-header">
              <div class="user-info">
                <el-avatar :size="40" :icon="UserFilled" />
                <div class="user-meta">
                  <span class="username">{{ comment.username }}</span>
                  <el-rate :model-value="comment.rating" disabled size="small" />
                </div>
              </div>
              <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
            </div>
            <p class="comment-content">{{ comment.content }}</p>
            <div class="comment-actions">
              <el-button
                link
                :icon="CaretTop"
                :type="comment.is_liked ? 'primary' : 'default'"
                :disabled="comment.is_liked"
                @click="likeComment(comment)"
              >
                {{ comment.is_liked ? '已赞' : '有用' }} ({{ comment.likes }})
              </el-button>
            </div>
          </div>

          <el-empty
            v-if="dish.comments?.length === 0"
            description="暂无评价，快来抢沙发吧！"
          />
        </div>

        <!-- 加载更多 -->
        <div class="load-more" v-if="dish.total_comments > dish.comments?.length">
          <el-button link @click="loadMoreComments">加载更多评价</el-button>
        </div>
      </div>
    </div>

    <!-- 评论对话框 -->
    <el-dialog
      v-model="showCommentDialog"
      title="撰写评价"
      width="500px"
      destroy-on-close
    >
      <el-form :model="commentForm" :rules="commentRules" ref="commentFormRef">
        <el-form-item label="评分" prop="rating">
          <el-rate
            v-model="commentForm.rating"
            show-score
            :max="5"
            size="large"
          />
        </el-form-item>
        <el-form-item label="评价内容" prop="content">
          <el-input
            v-model="commentForm.content"
            type="textarea"
            :rows="4"
            placeholder="分享你的用餐体验，帮助其他同学做出选择..."
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="commentForm.is_anonymous">匿名评价</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCommentDialog = false">取消</el-button>
        <el-button type="primary" @click="submitComment" :loading="submitting">
          提交评价
        </el-button>
      </template>
    </el-dialog>
  </div>

  <!-- 加载状态 -->
  <div v-else class="loading-container">
    <el-skeleton :rows="10" animated />
  </div>
</template>

<script setup>
import { ref, reactive, computed, inject, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Share, Star, Food, CircleCheck, MagicStick,
  ChatDotRound, UserFilled, CaretTop, Dish
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const { authState } = inject('auth')

const dish = ref(null)
const loading = ref(true)
const commentsLoading = ref(false)
const showCommentDialog = ref(false)
const submitting = ref(false)
const commentFormRef = ref(null)
const commentPage = ref(2)
const commentTotalPages = ref(1)
const ratingDistributionData = ref([])
const combo = ref({ combo_items: [] })
const comboLoading = ref(false)

const commentForm = reactive({
  rating: 5,
  content: '',
  is_anonymous: false
})

const commentRules = {
  rating: [{ required: true, message: '请选择评分', trigger: 'change' }],
  content: [
    { required: true, message: '请输入评价内容', trigger: 'blur' },
    { min: 2, max: 200, message: '评价长度应为2-200字', trigger: 'blur' }
  ]
}

// 计算评分统计（优先使用后端返回的分布数据）
const ratingStats = computed(() => {
  if (ratingDistributionData.value.length > 0) {
    return ratingDistributionData.value
  }
  if (!dish.value?.comments?.length) return []

  const stats = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 }
  const colors = {
    5: '#67c23a', 4: '#95d475', 3: '#e6a23c', 2: '#f89898', 1: '#f56c6c'
  }

  dish.value.comments.forEach(c => {
    const star = Math.floor(c.rating)
    if (stats[star] !== undefined) stats[star]++
  })

  const total = dish.value.comments.length
  return Object.entries(stats).map(([star, count]) => ({
    star: parseInt(star),
    count,
    percentage: Math.round((count / total) * 100),
    color: colors[star]
  })).reverse()
})

const getImageUrl = (photo) => {
  if (!photo) return ''
  if (photo.startsWith('http')) return photo
  return `/static/photos/${photo}`
}

const formatPath = (path) => {
  if (!path.entities || !path.relations) return []
  return path.entities.map((entity, idx) => ({
    entity,
    relation: path.relations[idx] || '',
    isLast: idx === path.entities.length - 1
  }))
}

const formatTime = (timestamp) => {
  if (!timestamp) return '未知时间'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  // 小于1小时显示"刚刚"等
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`

  return date.toLocaleDateString('zh-CN')
}

const goBack = () => {
  router.back()
}

const toggleFavorite = () => {
  ElMessage.success('收藏功能开发中')
}

const goToDetail = (dishId) => {
  if (!dishId || dishId === -1) {
    ElMessage.warning('菜品信息不完整')
    return
  }
  const id = parseInt(dishId)
  if (isNaN(id)) {
    ElMessage.error('无效的菜品ID')
    return
  }
  router.push(`/dish/${id}`)
}

const submitComment = async () => {
  const valid = await commentFormRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await axios.post(
      `/api/v1/dish/${route.params.id}/comment`,
      commentForm,
      { withCredentials: true }
    )

    ElMessage.success('评价提交成功')
    showCommentDialog.value = false

    // 重置表单
    commentForm.rating = 5
    commentForm.content = ''
    commentForm.is_anonymous = false

    // 刷新数据
    await loadDishDetail()
  } catch (err) {
    ElMessage.error(err.response?.data?.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

const likeComment = async (comment) => {
  if (comment.is_liked) {
    ElMessage.info('您已经点过赞了')
    return
  }
  try {
    const res = await axios.post(
      `/api/v1/dish/${route.params.id}/comment/${comment.comment_id}/like`,
      {},
      { withCredentials: true }
    )
    comment.likes = res.data.likes
    comment.is_liked = true
    ElMessage.success('点赞成功')
  } catch (err) {
    if (err.response?.status === 400) {
      comment.is_liked = true
      ElMessage.warning(err.response?.data?.msg || '您已经点过赞了')
    } else if (err.response?.status === 401) {
      ElMessage.warning('请先登录')
    } else {
      ElMessage.error(err.response?.data?.msg || '点赞失败')
    }
  }
}

const loadMoreComments = async () => {
  if (commentPage.value > commentTotalPages.value) {
    ElMessage.info('没有更多评论了')
    return
  }
  commentsLoading.value = true
  try {
    const res = await axios.get(
      `/api/v1/dish/${route.params.id}/comments?page=${commentPage.value}&per_page=10`,
      { withCredentials: true }
    )
    dish.value.comments.push(...res.data.comments)
    commentTotalPages.value = res.data.pages
    commentPage.value++
  } catch (err) {
    ElMessage.error('加载失败')
  } finally {
    commentsLoading.value = false
  }
}

const loadDishDetail = async () => {
  loading.value = true
  try {
    const [detailRes, statsRes] = await Promise.all([
      axios.get(`/api/v1/dish/${route.params.id}`, { withCredentials: true }),
      axios.get(`/api/v1/dish/${route.params.id}/rating-stats`, { withCredentials: true }).catch(() => null)
    ])
    dish.value = detailRes.data

    // 加载评分分布
    if (statsRes && statsRes.data) {
      const colors = { 5: '#67c23a', 4: '#95d475', 3: '#e6a23c', 2: '#f89898', 1: '#f56c6c' }
      const total = statsRes.data.total
      ratingDistributionData.value = Object.entries(statsRes.data.stats)
        .map(([star, count]) => ({
          star: parseInt(star),
          count,
          percentage: total > 0 ? Math.round((count / total) * 100) : 0,
          color: colors[star]
        }))
        .reverse()
    }

    // 重置评论分页
    commentPage.value = 2
    commentTotalPages.value = Math.ceil((dish.value.total_comments || 0) / 10)

    // 加载套餐推荐
    await loadCombo()
  } catch (err) {
    ElMessage.error(err.response?.data?.msg || '获取详情失败')
    router.push('/')
  } finally {
    loading.value = false
  }
}

const loadCombo = async () => {
  comboLoading.value = true
  try {
    const res = await axios.get(`/api/v1/dish/${route.params.id}/combo`, {
      withCredentials: true
    })
    combo.value = res.data
  } catch (err) {
    console.error('加载套餐推荐失败:', err)
    combo.value = { combo_items: [] }
  } finally {
    comboLoading.value = false
  }
}

onMounted(() => {
  loadDishDetail()
})
</script>

<style scoped>
.detail-container {
  min-height: 100vh;
  background: #f8fafc;
}

/* 导航栏 */
.detail-nav {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  z-index: 100;
}

.nav-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}

.nav-actions {
  display: flex;
  gap: 8px;
}

/* 主内容区 */
.detail-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 24px;
}

/* 左侧信息区 */
.info-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.image-gallery {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.main-image {
  position: relative;
  height: 400px;
}

.main-image img {
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
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  color: #9ca3af;
}

.price-badge {
  position: absolute;
  top: 20px;
  right: 20px;
  background: #f56c6c;
  color: #fff;
  padding: 8px 20px;
  border-radius: 24px;
  font-size: 24px;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
}

.info-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.dish-name {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 16px 0;
}

.rating-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.rating-count {
  color: #6b7280;
  font-size: 14px;
}

.tags-section,
.ingredients-section,
.explanation-section {
  margin-bottom: 24px;
}

.tags-section h4,
.ingredients-section h4,
.explanation-section h4 {
  font-size: 16px;
  color: #374151;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.ingredients-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.ingredient-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #4b5563;
  font-size: 14px;
}

.ingredient-item .el-icon {
  color: #67c23a;
}

/* 推荐理由 */
.explanation-section :deep(.el-alert) {
  margin-bottom: 16px;
}

.paths-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.path-item {
  background: #f9fafb;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.path-header {
  font-size: 13px;
  color: #667eea;
  font-weight: 600;
  margin-bottom: 10px;
}

.path-flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.node {
  background: #667eea;
  color: #fff;
  padding: 6px 14px;
  border-radius: 20px;
  font-weight: 500;
}

.node.start {
  background: #67c23a;
}

.node.end {
  background: #f56c6c;
}

.relation {
  background: #e6a23c;
  color: #fff;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.arrow {
  color: #9ca3af;
  font-weight: bold;
}

/* 右侧评论区 */
.comments-section {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  height: fit-content;
  position: sticky;
  top: 80px;
}

.comments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.comments-header h2 {
  font-size: 20px;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 评分分布 */
.rating-distribution {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.rating-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.star-label {
  width: 40px;
  font-size: 13px;
  color: #6b7280;
}

.progress-bar {
  flex: 1;
}

.count-label {
  width: 40px;
  text-align: right;
  font-size: 13px;
  color: #9ca3af;
}

/* 评论列表 */
.comments-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comment-item {
  padding-bottom: 20px;
  border-bottom: 1px solid #f3f4f6;
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.user-info {
  display: flex;
  gap: 12px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.username {
  font-weight: 600;
  color: #1a1a2e;
  font-size: 14px;
}

.comment-time {
  font-size: 12px;
  color: #9ca3af;
}

.comment-content {
  color: #4b5563;
  line-height: 1.6;
  margin: 0 0 12px 0;
  font-size: 14px;
}

.comment-actions {
  display: flex;
  gap: 16px;
}

.load-more {
  text-align: center;
  margin-top: 20px;
}

/* 加载状态 */
.loading-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 0 24px;
}

/* 智能搭配 */
.combo-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.combo-section h4 {
  font-size: 16px;
  color: #374151;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.combo-list {
  display: flex;
  align-items: stretch;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.combo-card {
  flex: 1;
  min-width: 140px;
  max-width: 200px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  cursor: pointer;
  transition: all 0.3s ease;
}

.combo-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.12);
}

.combo-card.main-card {
  border: 2px solid #67c23a;
  cursor: default;
}

.combo-card.main-card:hover {
  transform: none;
}

.combo-image {
  height: 100px;
  background: #f3f4f6;
  overflow: hidden;
}

.combo-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.combo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.combo-info {
  padding: 12px;
}

.combo-name {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.combo-price {
  font-size: 16px;
  font-weight: 700;
  color: #f56c6c;
  margin-bottom: 8px;
}

.combo-meta {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.combo-co {
  font-size: 11px;
  color: #667eea;
  background: #f5f3ff;
  padding: 2px 6px;
  border-radius: 8px;
}

.combo-plus {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: #9ca3af;
  padding: 0 4px;
}

.combo-summary {
  margin-top: 16px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.combo-total {
  font-size: 15px;
  color: #374151;
}

.combo-total strong {
  color: #f56c6c;
  font-size: 18px;
}

.combo-budget {
  font-size: 13px;
  color: #9ca3af;
}

/* 响应式 */
@media (max-width: 1024px) {
  .detail-content {
    grid-template-columns: 1fr;
  }

  .comments-section {
    position: static;
  }

  .combo-list {
    justify-content: center;
  }
}

@media (max-width: 640px) {
  .detail-content {
    padding: 16px;
  }

  .main-image {
    height: 280px;
  }

  .dish-name {
    font-size: 22px;
  }
}
</style>
