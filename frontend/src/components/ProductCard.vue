<template>
  <div class="card p-card" @click="$router.push(`/products/${p.id}`)">
    <img :src="p.cover" :alt="p.title" />
    <div class="p-body">
      <div class="p-title">{{ p.title }}</div>
      <div class="muted">{{ p.subtitle }}</div>
      <div class="p-foot">
        <span class="price">¥{{ p.price }}</span>
        <span class="muted">已售 {{ p.sales }}</span>
      </div>
      <el-button type="primary" size="small" @click.stop="add">加入购物车</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { bus, CART_CHANGED } from '../utils/eventBus'

const props = defineProps<{ p: any }>()

async function add() {
  try {
    await api.addCart({ product_id: props.p.id, quantity: 1 })
    ElMessage.success('已加入购物车')
    bus.emit(CART_CHANGED)
  } catch (e: any) {
    ElMessage.warning(e.response?.data?.msg || '请先登录')
  }
}
</script>

<style scoped>
.p-card { cursor: pointer; overflow: hidden; transition: transform .15s; }
.p-card:hover { transform: translateY(-3px); }
.p-card img { width: 100%; height: 170px; object-fit: cover; }
.p-body { padding: 12px; }
.p-title { font-weight: 600; margin-bottom: 4px; height: 40px; overflow: hidden; }
.p-foot { display: flex; justify-content: space-between; align-items: center; margin: 8px 0; }
.p-body .el-button { width: 100%; }
</style>
