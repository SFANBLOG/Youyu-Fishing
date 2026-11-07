<template>
  <div style="display:flex;gap:14px">
    <aside class="card" style="width:250px;padding:10px;flex-shrink:0">
      <h3 style="margin:8px">提示词列表</h3>
      <div v-for="p in rows" :key="p.id" class="p-item" :class="{active: current?.id === p.id}"
           @click="select(p)">
        <b>{{ p.name }}</b>
        <div class="muted">{{ p.key }}</div>
      </div>
    </aside>

    <section class="card" style="flex:1;padding:18px" v-if="current">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <h2 style="margin:0">{{ current.name }}</h2>
        <el-button type="primary" @click="save">保存并即时生效</el-button>
      </div>
      <div class="muted" style="margin:6px 0 14px">
        变量：{{ (current.variables || []).join('、') || '无' }} ｜ 用花括号占位，如 {query}
      </div>
      <el-input v-model="current.content" type="textarea" :rows="14" />
      <div style="display:flex;gap:8px;align-items:center;margin-top:14px">
        <el-input v-model="previewQuery" placeholder="给变量填个示例值（如 query）" style="width:300px" />
        <el-button @click="preview">变量渲染预览</el-button>
      </div>
      <div v-if="rendered" class="card" style="margin-top:12px;padding:14px;white-space:pre-wrap;background:#f9fafb">
        {{ rendered }}
      </div>
      <div v-if="missing?.length" class="muted" style="margin-top:6px">未替换变量：{{ missing.join('、') }}</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../../api'

const rows = ref<any[]>([])
const current = ref<any>(null)
const previewQuery = ref('新手选什么竿')
const rendered = ref('')
const missing = ref<string[]>([])

function select(p: any) { current.value = { ...p }; rendered.value = ''; missing.value = [] }
async function load() {
  const r: any = await api.prompts()
  rows.value = r.data || []
  if (rows.value.length && !current.value) select(rows.value[0])
}
async function save() {
  await api.updatePrompt(current.value.id, {
    key: current.value.key, name: current.value.name,
    content: current.value.content, variables: current.value.variables,
    enabled: current.value.enabled,
  })
  ElMessage.success('已保存，下一次对话即生效')
  load()
}
async function preview() {
  const vars: any = {}
  ;(current.value.variables || []).forEach((v: string) => { vars[v] = previewQuery.value })
  const r: any = await api.previewPrompt(current.value.id, vars)
  rendered.value = r.data.rendered
  missing.value = r.data.missing
}
onMounted(load)
</script>

<style scoped>
.p-item { padding: 10px; border-radius: 8px; cursor: pointer; margin-bottom: 6px; }
.p-item:hover { background: #f3f4f6; }
.p-item.active { background: #ccfbf1; }
</style>
