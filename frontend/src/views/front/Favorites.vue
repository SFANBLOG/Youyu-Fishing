<template>
  <div>
    <h2 class="section-title">我的收藏</h2>
    <div class="grid-products">
      <ProductCard v-for="p in items" :key="p.id" :p="p" />
    </div>
    <el-empty v-if="!items.length" description="还没有收藏商品" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../../api'
import ProductCard from '../../components/ProductCard.vue'
const items = ref<any[]>([])
onMounted(async () => {
  const r: any = await api.favorites()
  items.value = r.data || []
})
</script>
