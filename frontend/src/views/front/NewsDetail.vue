<template>
  <div class="card" style="padding:28px;margin-top:20px;max-width:900px;margin-left:auto;margin-right:auto" v-if="n">
    <h1>{{ n.title }}</h1>
    <div class="muted" style="margin-bottom:20px">{{ n.views }} 次阅读</div>
    <div v-html="n.content"></div>
    <el-button style="margin-top:24px" @click="$router.back()">返回</el-button>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api'
const route = useRoute()
const n = ref<any>(null)
onMounted(async () => {
  const r: any = await api.newsDetail(Number(route.params.id))
  n.value = r.data
})
</script>
