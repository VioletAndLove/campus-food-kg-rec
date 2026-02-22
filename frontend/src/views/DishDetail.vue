<template>
  <div class="container" v-if="dish">
    <el-button @click="$router.back()">返回</el-button>
    <el-card class="detail-card">
      <h2>{{ dish.name }}</h2>
      <p class="price">¥{{ dish.price }}</p>

      <div class="section">
        <h4>口味标签</h4>
        <el-tag v-for="tag in dish.tags" :key="tag" class="tag-item">{{ tag }}</el-tag>
      </div>

      <div class="section">
        <h4>食材</h4>
        <p>{{ dish.ingredients?.join('、') || '暂无信息' }}</p>
      </div>

      <div class="section" v-if="dish.photo && !imageError">
        <h4>菜品照片</h4>
        <img :src="getImageUrl(dish.photo)" @error="handleImageError" class="dish-image" />
      </div>
      <div class="section no-photo" v-else-if="!dish.photo || imageError">
        <el-empty description="暂无照片" :image-size="100" />
      </div>

      <!-- 推荐理由 -->
      <div class="section explanation-section" v-if="dish.explanation">
        <h4>推荐理由</h4>
        <el-alert :title="dish.explanation" type="success" :closable="false" show-icon />
      </div>

      <!-- 推理路径 -->
      <div class="section paths-section" v-if="dish.paths?.length > 0">
        <h4>推理路径（{{ dish.paths.length }}条）</h4>
        <div v-for="(path, index) in dish.paths" :key="index" class="path-card">
          <div class="path-header">路径 {{ index + 1 }}：{{ path.pattern }}</div>
          <div class="path-flow">
            <span class="path-node user">您</span>
            <span v-for="(step, idx) in formatPath(path)" :key="idx" class="path-step">
              <span class="arrow">→</span>
              <span class="relation">{{ step.relation }}</span>
              <span class="arrow">→</span>
              <span class="path-node" :class="{ target: step.isLast }">{{ step.entity }}</span>
            </span>
          </div>
        </div>
      </div>

      <!-- 用户反馈 -->
      <div class="section feedback-section">
        <h4>您对这道推荐满意吗？</h4>
        <div class="rating-stars">
          <el-rate
            v-model="feedback.rating"
            :max="5"
            show-score
            text-color="#ff9900"
            score-template="{value}分"
          />
        </div>
        <el-input
          v-model="feedback.comment"
          type="textarea"
          :rows="2"
          placeholder="请输入您的建议（可选）"
          class="feedback-input"
        />
        <el-button
          type="primary"
          @click="submitFeedback"
          :loading="feedback.submitting"
          :disabled="feedback.rating === 0"
        >
          提交评价
        </el-button>
        <el-alert
          v-if="feedback.submitted"
          title="评价已提交，谢谢！"
          type="success"
          :closable="false"
          class="feedback-success"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const route = useRoute()
const dish = ref(null)
const imageError = ref(false)

const feedback = ref({
  rating: 0,
  comment: '',
  submitting: false,
  submitted: false
})

const getImageUrl = (photo) => {
  if (!photo) return ''
  if (photo.startsWith('http')) return photo
  return `http://localhost:5000/static/photos/${photo}`
}

const handleImageError = () => {
  imageError.value = true
}

const formatPath = (path) => {
  if (!path.entities || !path.relations) return []
  return path.entities.map((entity, idx) => ({
    entity,
    relation: path.relations[idx] || '',
    isLast: idx === path.entities.length - 1
  }))
}

const submitFeedback = async () => {
  if (feedback.value.rating === 0) {
    ElMessage.warning('请先选择评分')
    return
  }

  feedback.value.submitting = true
  try {
    const token = localStorage.getItem('token')
    await axios.post('http://localhost:5000/api/v1/feedback/', {
      dish_id: parseInt(route.params.id),
      rating: feedback.value.rating,
      clicked: true,
      comment: feedback.value.comment
    }, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    feedback.value.submitted = true
    ElMessage.success('评价提交成功')
  } catch (err) {
    ElMessage.error(err.response?.data?.msg || '提交失败')
  } finally {
    feedback.value.submitting = false
  }
}

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`http://localhost:5000/api/v1/dish/${route.params.id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    dish.value = res.data
  } catch (err) {
    console.error('获取菜品详情失败:', err)
    ElMessage.error('获取详情失败')
  }
})
</script>

<style scoped>
.container { max-width: 800px; margin: 0 auto; padding: 20px; }
.detail-card { margin-top: 20px; }
.price { font-size: 28px; color: #f56c6c; font-weight: bold; margin: 15px 0; }
.section { margin: 20px 0; }
.section h4 { margin-bottom: 12px; color: #303133; font-size: 16px; }
.tag-item { margin-right: 8px; margin-bottom: 5px; }
.dish-image { max-width: 100%; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
.no-photo { padding: 20px; background: #f5f7fa; border-radius: 8px; }

.explanation-section { background: #f0f9eb; padding: 15px; border-radius: 8px; border-left: 4px solid #67c23a; }
.paths-section { margin-top: 25px; }
.path-card { background: #f5f7fa; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e4e7ed; }
.path-header { font-weight: bold; color: #409eff; margin-bottom: 10px; font-size: 13px; }
.path-flow { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; font-size: 13px; }
.path-step { display: flex; align-items: center; gap: 4px; }
.path-node { background: #409eff; color: white; padding: 4px 10px; border-radius: 12px; font-weight: 500; }
.path-node.user { background: #67c23a; }
.path-node.target { background: #f56c6c; }
.relation { background: #e6a23c; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
.arrow { color: #909399; font-weight: bold; }

.feedback-section {
  background: #fdf6ec;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #f3d19e;
  margin-top: 30px;
}
.rating-stars { margin: 15px 0; }
.feedback-input { margin: 15px 0; }
.feedback-success { margin-top: 15px; }
</style>
