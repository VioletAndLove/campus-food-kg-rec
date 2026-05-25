<template>
  <div class="dish-card" :class="{ 'is-recommendation': isRecommendation }" @click="$emit('click')">
    <div class="card-image">
      <img v-if="dish.photo" :src="getImageUrl(dish.photo)" :alt="dish.dish_name || dish.name" @error="handleImageError" />
      <div v-else class="placeholder-image">
        <el-icon :size="40"><Food /></el-icon>
      </div>
      <div class="price-tag">¥{{ dish.price }}</div>
      <div v-if="isRecommendation && dish.score" class="score-badge">
        <el-icon><StarFilled /></el-icon>
        {{ dish.score.toFixed(1) }}
      </div>
    </div>

    <div class="card-content">
      <h3 class="dish-name">{{ dish.dish_name || dish.name }}</h3>

      <div class="dish-tags" v-if="dish.tags?.length">
        <el-tag
          v-for="tag in dish.tags.slice(0, 3)"
          :key="tag"
          size="small"
          effect="plain"
        >
          {{ tag }}
        </el-tag>
      </div>

      <div class="dish-ingredients" v-if="dish.ingredients?.length">
        <el-icon :size="12"><Food /></el-icon>
        <span>{{ dish.ingredients.slice(0, 3).join('、') }}</span>
      </div>

      <div v-if="dish.explanation" class="explanation">
        <el-icon :size="12"><InfoFilled /></el-icon>
        <span>{{ truncate(dish.explanation, 30) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Food, StarFilled, InfoFilled } from '@element-plus/icons-vue'

defineProps({
  dish: {
    type: Object,
    required: true
  },
  isRecommendation: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

const getImageUrl = (photo) => {
  if (!photo) return ''
  if (photo.startsWith('http')) return photo
  return `/static/photos/${photo}`
}

const handleImageError = (e) => {
  e.target.style.display = 'none'
  e.target.nextElementSibling.style.display = 'flex'
}

const truncate = (str, len) => {
  if (!str) return ''
  return str.length > len ? str.substring(0, len) + '...' : str
}
</script>

<style scoped>
.dish-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.dish-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.15);
}

.dish-card.is-recommendation {
  border: 2px solid transparent;
}

.dish-card.is-recommendation:hover {
  border-color: #667eea;
}

.card-image {
  position: relative;
  height: 180px;
  overflow: hidden;
  background: #f3f4f6;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.dish-card:hover .card-image img {
  transform: scale(1.05);
}

.placeholder-image {
  width: 100%;
  height: 100%;
  display: none;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
}

.price-tag {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(245, 108, 108, 0.95);
  color: #fff;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.score-badge {
  position: absolute;
  bottom: 12px;
  left: 12px;
  background: rgba(102, 126, 234, 0.95);
  color: #fff;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-content {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dish-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.dish-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.dish-ingredients,
.explanation {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
}

.explanation {
  color: #667eea;
  background: #f5f3ff;
  padding: 6px 10px;
  border-radius: 8px;
  margin-top: auto;
}
</style>
