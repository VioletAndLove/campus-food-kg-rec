<template>
  <div class="container">
    <h1>校园美食推荐系统</h1>

    <!-- 登录状态栏 -->
    <div class="auth-section" v-if="!isLoggedIn">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-input v-model="loginForm.username" placeholder="用户名" style="width: 200px; margin: 5px"/>
          <el-input v-model="loginForm.password" placeholder="密码" type="password" style="width: 200px; margin: 5px"/>
          <el-button type="primary" @click="handleLogin">登录</el-button>
        </el-tab-pane>
        <el-tab-pane label="注册" name="register">
          <el-input v-model="registerForm.username" placeholder="用户名" style="width: 200px; margin: 5px"/>
          <el-input v-model="registerForm.password" placeholder="密码" type="password" style="width: 200px; margin: 5px"/>
          <el-button type="success" @click="handleRegister">注册</el-button>
        </el-tab-pane>
      </el-tabs>
    </div>

    <div class="auth-section" v-else>
      <span>欢迎，{{ currentUser.username }}</span>
      <el-button type="info" size="small" @click="logout" style="margin-left: 10px">退出</el-button>
    </div>

    <!-- 推荐功能 -->
    <div class="input-section" v-if="isLoggedIn">
      <el-input-number v-model="topk" :min="1" :max="100" :value="10" style="margin-right: 10px"/>
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
import { ref, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 认证状态
const activeTab = ref('login')
const token = ref(localStorage.getItem('token') || '')
const currentUser = ref(JSON.parse(localStorage.getItem('user') || '{}'))

const isLoggedIn = computed(() => !!token.value)

const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ username: '', password: '' })

// 推荐状态
const topk = ref(10)
const loading = ref(false)
const recommendations = ref([])
const fromCache = ref(false)

// 设置 axios 默认头
if (token.value) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
}

const handleLogin = async () => {
  try {
    const response = await axios.post('http://localhost:5000/api/v1/auth/login', loginForm.value)
    token.value = response.data.access_token
    currentUser.value = {
      user_id: response.data.user_id,
      username: response.data.username
    }
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(currentUser.value))
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    ElMessage.success('登录成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '登录失败')
  }
}

const handleRegister = async () => {
  try {
    const response = await axios.post('http://localhost:5000/api/v1/auth/register', registerForm.value)
    token.value = response.data.access_token
    currentUser.value = {
      user_id: response.data.user_id,
      username: response.data.username
    }
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(currentUser.value))
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    ElMessage.success('注册成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '注册失败')
  }
}

const logout = () => {
  token.value = ''
  currentUser.value = {}
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  delete axios.defaults.headers.common['Authorization']
  recommendations.value = []
  ElMessage.info('已退出')
}

const getRecommendations = async () => {
  loading.value = true
  try {
    const response = await axios.post('http://localhost:5000/api/v1/rec/', {
      user_id: currentUser.value.user_id,
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

.auth-section {
  margin: 20px 0;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
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
