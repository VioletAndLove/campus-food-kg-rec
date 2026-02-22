<template>
  <div class="container">
    <h1>校园美食推荐系统</h1>

    <div v-if="!isLoggedIn" class="auth-tip">
      <el-alert title="请先登录获取个性化推荐" type="info" show-icon />
      <el-button type="primary" @click="$router.push('/login')" style="margin-top: 10px;">去登录</el-button>
    </div>

    <div v-else class="input-section">
      <el-input-number v-model="topk" :min="1" :max="20" :value="10" />
      <el-button type="primary" @click="getRecommendations" :loading="loading">获取推荐</el-button>
    </div>

    <div v-if="recommendations.length > 0" class="result-section">
      <h3>推荐结果 {{ fromCache ? '（来自缓存）' : '（实时计算）' }}</h3>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8" v-for="item in recommendations" :key="item.dish_id">
          <el-card class="dish-card" @click="goToDetail(item.dish_id)" shadow="hover">
            <div class="dish-header">
              <span class="dish-name">{{ item.dish_name }}</span>
              <span class="dish-price">¥{{ item.price }}</span>
            </div>
            <div class="dish-tags">
              <el-tag v-for="tag in item.tags?.slice(0,3)" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
            </div>
            <div class="dish-score">推荐分：{{ item.score?.toFixed(2) || '0.00' }}</div>
            <div class="explanation-preview" v-if="item.explanation">
              <el-icon size="12"><Info-Filled /></el-icon>
              <span>{{ truncate(item.explanation, 25) }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-empty v-else-if="!loading && isLoggedIn" description="点击按钮获取推荐" />
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'

const router = useRouter()
const { token, currentUser, isLoggedIn } = inject('auth')

const topk = ref(10)
const loading = ref(false)
const recommendations = ref([])
const fromCache = ref(false)

const truncate = (str, len) => {
  if (!str) return ''
  return str.length > len ? str.substring(0, len) + '...' : str
}

const getRecommendations = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    return
  }

  loading.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/v1/rec/', {
      user_id: currentUser.value.user_id,
      topk: topk.value
    }, {
      headers: { 'Authorization': `Bearer ${token.value}` }
    })
    recommendations.value = res.data.recommendations || []
    fromCache.value = res.data.from_cache
  } catch (err) {
    ElMessage.error(err.response?.data?.message || '获取推荐失败')
  } finally {
    loading.value = false
  }
}

const goToDetail = (dishId) => {
  router.push(`/dish/${dishId}`)
}
</script>

<style scoped>
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.auth-tip { text-align: center; padding: 40px; background: #f5f7fa; border-radius: 8px; margin: 20px 0; }
.input-section { margin: 20px 0; display: flex; gap: 10px; align-items: center; }
.dish-card { margin-bottom: 20px; cursor: pointer; transition: all 0.3s; }
.dish-card:hover { transform: translateY(-5px); }
.dish-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.dish-name { font-size: 16px; font-weight: bold; color: #303133; }
.dish-price { font-size: 18px; color: #f56c6c; font-weight: bold; }
.dish-tags { margin: 8px 0; display: flex; flex-wrap: wrap; gap: 5px; }
.dish-score { color: #409eff; font-size: 13px; margin: 5px 0; }
.explanation-preview {
  margin-top: 8px;
  padding: 6px 10px;
  background: #f0f9eb;
  border-radius: 4px;
  font-size: 12px;
  color: #67c23a;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
