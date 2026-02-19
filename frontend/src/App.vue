<template>
  <div class="container">
    <h1>校园美食推荐系统</h1>

    <div class="input-section">
      <el-input v-model="userId" placeholder="用户ID (0-499)" style="width: 200px; margin-right: 10px"/>
      <el-input-number v-model="topk" :min="1" :max="20" :value="10" style="margin-right: 10px"/>
      <el-button type="primary" @click="getRecommendations" :loading="loading">获取推荐</el-button>
    </div>

    <div v-if="recommendations.length > 0" class="result-section">
      <h3>推荐结果 ({{ fromCache ? '来自缓存' : '实时计算' }})</h3>
      <el-row :gutter="20">
        <el-col :span="8" v-for="item in recommendations" :key="item.dish_id">
          <el-card class="dish-card" :body-style="{ padding: '15px' }">
            <div class="dish-header">
              <span class="dish-name">{{ item.dish_name }}</span>
              <span class="dish-price">¥{{ item.price }}</span>
            </div>
            <div class="dish-tags">
              <el-tag v-for="tag in item.tags" :key="tag" size="small" style="margin: 2px">{{ tag }}</el-tag>
            </div>
            <div class="dish-ingredients">
              <p>食材: {{ item.ingredients.join('、') }}</p>
            </div>
            <div class="dish-score">
              <span>推荐分: {{ item.score.toFixed(2) }}</span>
            </div>
            <div v-if="item.photo" class="dish-photo">
              <img :src="`http://localhost:5000/static/photos/${item.photo}`" :alt="item.dish_name" @error="handleImageError"/>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const userId = ref('0')
const topk = ref(10)
const loading = ref(false)
const recommendations = ref([])
const fromCache = ref(false)

const getRecommendations = async () => {
  loading.value = true
  try {
    const response = await axios.post('http://localhost:5000/api/v1/rec/', {
      user_id: parseInt(userId.value),
      topk: topk.value
    })
    recommendations.value = response.data.recommendations
    fromCache.value = response.data.from_cache
  } catch (error) {
    ElMessage.error('获取推荐失败: ' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

const handleImageError = (e) => {
  e.target.style.display = 'none'
}
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.input-section {
  margin: 20px 0;
  display: flex;
  align-items: center;
}

.result-section {
  margin-top: 30px;
}

.dish-card {
  margin-bottom: 20px;
  transition: transform 0.2s;
}

.dish-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.dish-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.dish-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.dish-price {
  font-size: 18px;
  color: #f56c6c;
  font-weight: bold;
}

.dish-tags {
  margin: 10px 0;
}

.dish-ingredients {
  font-size: 13px;
  color: #606266;
  margin: 10px 0;
}

.dish-score {
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
}

.dish-photo img {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 4px;
  margin-top: 10px;
}
</style>
