<template>
  <div>
    <h2 class="section-title">钓鱼资讯</h2>
    <div class="card" style="padding:8px 24px">
      <div v-for="n in items" :key="n.id" style="padding:18px 0;border-bottom:1px solid #f3f4f6;cursor:pointer"
           @click="$router.push(`/news/${n.id}`)">
        <h3 style="margin:0 0 6px">{{ n.title }}</h3>
        <div class="muted">{{ n.summary }}</div>
        <div class="muted" style="margin-top:6px">{{ n.created_at }} · {{ n.views }} 次阅读</div>
      </div>
      <el-empty v-if="!items.length" description="暂无资讯" />
    </div>
    <div style="display:flex;justify-content:center;margin:20px">
      <el-pagination background layout="prev, pager, next" :total="total"
                     v-model:current-page="page" v-model:page-size="size" @current-change="load" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../../api'
const items = ref<any[]>([])
const total = ref(0), page = ref(1), size = ref(10)
async function load() {
  const r: any = await api.news({ page: page.value, size: size.value })
  items.value = r.data?.items || []
  total.value = r.data?.total || 0
}
onMounted(load)
</script>
