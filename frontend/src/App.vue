<template>
  <div class="app">
    <el-menu :default-active="$route.path" router mode="horizontal">
      <el-menu-item index="/">首页</el-menu-item>
      <el-menu-item index="/history">历史记录</el-menu-item>
      <el-menu-item index="/profile">个人中心</el-menu-item>
      <el-menu-item v-if="!isLoggedIn" index="/login">登录</el-menu-item>
      <el-menu-item v-else @click="logout">退出 ({{ currentUser.username }})</el-menu-item>
    </el-menu>

    <router-view />
  </div>
</template>

<script setup>
import { ref, computed, provide } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const token = ref(localStorage.getItem('token') || '')
const currentUser = ref(JSON.parse(localStorage.getItem('user') || '{}'))

const isLoggedIn = computed(() => !!token.value)

const logout = () => {
  token.value = ''
  currentUser.value = {}
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/')
}

// 全局提供登录状态
provide('auth', {
  token,
  currentUser,
  isLoggedIn,
  logout
})
</script>
