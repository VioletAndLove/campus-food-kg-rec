<template>
  <div class="login-container">
    <div class="login-wrapper">
      <!-- 左侧品牌区域 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="logo">
            <el-icon :size="64" color="#fff"><Food /></el-icon>
          </div>
          <h1 class="brand-title">校园美食推荐</h1>
          <p class="brand-subtitle">基于知识图谱的智能推荐系统</p>
          <div class="brand-features">
            <div class="feature-item">
              <el-icon><CircleCheck /></el-icon>
              <span>个性化推荐</span>
            </div>
            <div class="feature-item">
              <el-icon><CircleCheck /></el-icon>
              <span>可解释路径</span>
            </div>
            <div class="feature-item">
              <el-icon><CircleCheck /></el-icon>
              <span>多维度筛选</span>
            </div>
          </div>
        </div>
        <div class="brand-decoration">
          <div class="decoration-circle c1"></div>
          <div class="decoration-circle c2"></div>
          <div class="decoration-circle c3"></div>
        </div>
      </div>

      <!-- 右侧表单区域 -->
      <div class="form-section">
        <div class="form-container">
          <div class="form-header">
            <h2>{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
            <p>{{ isLogin ? '登录以获取个性化推荐' : '注册开始您的美食之旅' }}</p>
          </div>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="login-form"
            @keyup.enter="handleSubmit"
          >
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                :prefix-icon="User"
                size="large"
                clearable
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                size="large"
                show-password
                clearable
              />
            </el-form-item>

            <el-form-item prop="confirmPassword" v-if="!isLogin">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="请确认密码"
                :prefix-icon="Lock"
                size="large"
                show-password
                clearable
              />
            </el-form-item>

            <div class="form-options" v-if="isLogin">
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
              <el-link type="primary" :underline="false">忘记密码？</el-link>
            </div>

            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="handleSubmit"
            >
              {{ isLogin ? '立即登录' : '立即注册' }}
            </el-button>

            <div class="form-footer">
              <span>{{ isLogin ? '还没有账号？' : '已有账号？' }}</span>
              <el-link
                type="primary"
                :underline="false"
                @click="toggleMode"
              >
                {{ isLogin ? '立即注册' : '立即登录' }}
              </el-link>
            </div>
          </el-form>

          <!-- 游客入口 -->
          <div class="guest-entry">
            <el-divider>
              <span class="divider-text">或者</span>
            </el-divider>
            <el-button
              size="large"
              class="guest-btn"
              @click="enterAsGuest"
            >
              <el-icon><UserFilled /></el-icon>
              游客浏览（无推荐功能）
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, inject } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Food, User, Lock, UserFilled, CircleCheck } from '@element-plus/icons-vue'

const router = useRouter()
const { updateAuthState } = inject('auth')

const formRef = ref(null)
const loading = ref(false)
const isLogin = ref(true)
const rememberMe = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (!isLogin.value && value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应为6-20位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: !isLogin.value, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const endpoint = isLogin.value ? '/api/v1/auth/login' : '/api/v1/auth/register'
    const res = await axios.post(`${endpoint}`, {
      username: form.username,
      password: form.password
    }, {
      withCredentials: true  // 重要：允许携带session cookie
    })

    updateAuthState({
      user_id: res.data.user_id,
      username: res.data.username,
      is_logged_in: true
    })

    ElMessage.success(isLogin.value ? '登录成功' : '注册成功')
    router.push('/')
  } catch (err) {
    ElMessage.error(err.response?.data?.message || '操作失败，请重试')
  } finally {
    loading.value = false
  }
}

const enterAsGuest = () => {
  updateAuthState({
    user_id: 0,
    username: '游客',
    is_logged_in: false
  })
  ElMessage.info('以游客身份浏览，推荐功能需登录后使用')
  router.push('/')
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-wrapper {
  display: flex;
  width: 100%;
  max-width: 1000px;
  min-height: 600px;
  background: #fff;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* 左侧品牌区域 */
.brand-section {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  overflow: hidden;
}

.brand-content {
  position: relative;
  z-index: 2;
  color: #fff;
  text-align: center;
}

.logo {
  width: 100px;
  height: 100px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 30px;
  backdrop-filter: blur(10px);
}

.brand-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 12px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.brand-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 40px;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  opacity: 0.9;
}

.brand-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.c1 {
  width: 300px;
  height: 300px;
  top: -100px;
  right: -100px;
}

.c2 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  left: -50px;
}

.c3 {
  width: 150px;
  height: 150px;
  top: 50%;
  left: 30%;
  background: rgba(255, 255, 255, 0.05);
}

/* 右侧表单区域 */
.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: #fff;
}

.form-container {
  width: 100%;
  max-width: 360px;
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.form-header h2 {
  font-size: 28px;
  color: #1a1a2e;
  margin-bottom: 8px;
  font-weight: 600;
}

.form-header p {
  color: #6b7280;
  font-size: 14px;
}

.login-form {
  margin-bottom: 24px;
}

:deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 4px 15px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

:deep(.el-input__inner) {
  height: 44px;
  font-size: 14px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0;
  font-size: 13px;
}

.submit-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.form-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #6b7280;
}

.form-footer .el-link {
  font-weight: 500;
  margin-left: 4px;
}

/* 游客入口 */
.guest-entry {
  margin-top: 20px;
}

.divider-text {
  color: #9ca3af;
  font-size: 12px;
}

.guest-btn {
  width: 100%;
  height: 44px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.guest-btn:hover {
  border-color: #667eea;
  color: #667eea;
  background: #f5f3ff;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-wrapper {
    flex-direction: column;
  }

  .brand-section {
    padding: 40px 20px;
    min-height: 200px;
  }

  .brand-title {
    font-size: 28px;
  }

  .form-section {
    padding: 40px 20px;
  }
}
</style>
