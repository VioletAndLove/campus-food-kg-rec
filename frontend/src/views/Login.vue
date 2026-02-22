<template>
  <div class="container">
    <el-card class="login-card">
      <h2>用户登录</h2>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" label-position="top">
            <el-form-item label="用户名">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleLogin" :loading="loading">登录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" label-position="top">
            <el-form-item label="用户名">
              <el-input v-model="registerForm.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="success" @click="handleRegister" :loading="loading">注册</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const { token, currentUser, isLoggedIn } = inject('auth')

const activeTab = ref('login')
const loading = ref(false)

const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ username: '', password: '' })

const handleLogin = async () => {
  loading.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/v1/auth/login', loginForm.value)
    token.value = res.data.access_token
    currentUser.value = {
      user_id: res.data.user_id,
      username: res.data.username
    }
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(currentUser.value))
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    ElMessage.success('登录成功')
    router.push('/')
  } catch (err) {
    ElMessage.error(err.response?.data?.message || '登录失败')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  loading.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/v1/auth/register', registerForm.value)
    token.value = res.data.access_token
    currentUser.value = {
      user_id: res.data.user_id,
      username: res.data.username
    }
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(currentUser.value))
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    ElMessage.success('注册成功')
    router.push('/')
  } catch (err) {
    ElMessage.error(err.response?.data?.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.container {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
}
.login-card {
  padding: 20px;
}
h2 {
  text-align: center;
  margin-bottom: 20px;
}
</style>
