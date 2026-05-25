<template>
  <router-view v-slot="{ Component }">
    <keep-alive include="Home">
      <component :is="Component" />
    </keep-alive>
  </router-view>
</template>

<script setup>
import { provide, ref, onMounted } from 'vue'
import axios from 'axios'

const authState = ref({
  user_id: 0,
  username: '',
  is_logged_in: false,
  history_count: 0
})

const updateAuthState = (newState) => {
  authState.value = { ...authState.value, ...newState }
}

const checkAuthStatus = async () => {
  try {
    const res = await axios.get('/api/v1/auth/status', {
      withCredentials: true
    })
    if (res.data.is_logged_in) {
      updateAuthState({
        user_id: res.data.user_id,
        username: res.data.username,
        is_logged_in: true,
        history_count: res.data.history_count
      })
    }
  } catch (err) {
    console.log('未登录状态')
  }
}

const logout = async () => {
  try {
    await axios.post('/api/v1/auth/logout', {}, {
      withCredentials: true
    })
    updateAuthState({
      user_id: 0,
      username: '',
      is_logged_in: false,
      history_count: 0
    })
  } catch (err) {
    console.error('退出失败:', err)
  }
}

onMounted(() => {
  checkAuthStatus()
})

provide('auth', {
  authState,
  updateAuthState,
  logout,
  checkAuthStatus
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f5f7fa;
}
</style>
