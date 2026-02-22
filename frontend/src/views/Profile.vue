<template>
  <div class="container">
    <h2>个人中心</h2>
    <p>用户名: {{ currentUser?.username }}</p>
    <p>用户ID: {{ currentUser?.user_id }}</p>
  </div>
</template>

<script setup>
import { inject } from 'vue'
const { currentUser } = inject('auth')
</script>
