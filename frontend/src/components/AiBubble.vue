<template>
  <div class="bubble" :class="role === 'user' ? 'user' : 'ai'">
    <div v-if="images?.length" class="chat-images">
      <img v-for="(img, i) in images" :key="i" :src="img" />
    </div>
    <div v-if="role === 'user'">{{ text }}</div>
    <!-- 流式期间用纯文本，结束后一次性做 Markdown + 代码高亮 -->
    <div v-else-if="streaming" class="stream-plain">{{ text }}</div>
    <div v-else v-html="renderMarkdown(text)"></div>

    <div v-if="recommendations?.length" class="product-cards">
      <div v-for="p in recommendations" :key="p.id" class="product-mini" @click="go(p.id)">
        <img :src="p.cover" />
        <div>{{ p.title }}</div>
        <div class="price">¥{{ p.price }}</div>
      </div>
    </div>

    <div v-if="sources?.length" class="muted" style="margin-top:10px">
      引用：
      <el-tag v-for="s in sources" :key="s.chunk_id" size="small" style="margin-right:4px">
        {{ s.doc_title }} #{{ s.idx + 1 }}
      </el-tag>
    </div>
    <div v-if="meta" class="muted" style="margin-top:6px">
      {{ meta }}
      <el-tag v-if="degraded" type="warning" size="small">离线兜底</el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { renderMarkdown } from '../utils/markdown'

defineProps<{
  role: 'user' | 'assistant'
  text: string
  streaming?: boolean
  images?: string[]
  recommendations?: any[]
  sources?: any[]
  meta?: string
  degraded?: boolean
}>()
const router = useRouter()
const go = (id: number) => router.push(`/products/${id}`)
</script>

<style scoped>
.chat-images { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.chat-images img { width: 110px; height: 90px; object-fit: cover; border-radius: 8px; }
.product-mini { cursor: pointer; }
</style>
