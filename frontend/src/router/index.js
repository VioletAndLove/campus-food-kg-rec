import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/HomeView.vue'
import DishDetail from '../views/DishDetail.vue'
import History from '../views/History.vue'
import Profile from '../views/Profile.vue'
import Login from '../views/Login.vue'  // 新增

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/dish/:id', name: 'DishDetail', component: DishDetail, props: true },
  { path: '/history', name: 'History', component: History },
  { path: '/profile', name: 'Profile', component: Profile },
  { path: '/login', name: 'Login', component: Login }  // 新增
]

export default createRouter({
  history: createWebHistory(),
  routes
})
