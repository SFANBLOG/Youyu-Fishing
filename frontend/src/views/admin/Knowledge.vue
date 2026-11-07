<template>
  <div>
    <div class="card" style="padding:18px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <div>
          <h2 style="margin:0">知识库管理</h2>
          <div class="muted">自动切片：300 字窗口 + 60 字重叠；支持重建索引、切片预览与检索测试</div>
        </div>
        <el-button type="primary" @click="open()">新增文档</el-button>
      </div>

      <el-table :data="docs" border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="filename" label="文件名" width="160" />
        <el-table-column prop="chunk_count" label="切片数" width="90" />
        <el-table-column prop="size" label="字符数" width="100" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{row}">
            <el-button size="small" @click="showChunks(row)">切片预览</el-button>
            <el-button size="small" @click="reindex(row)">重建索引</el-button>
            <el-button size="small" @click="open(row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="card" style="padding:18px;margin-top:16px">
      <h3 style="margin:0 0 10px">检索测试</h3>
      <div style="display:flex;gap:8px">
        <el-input v-model="query" placeholder="输入一个知识类问题，如：新手选什么调性的竿" />
        <el-input-number v-model="topK" :min="1" :max="10" />
        <el-button type="primary" @click="searchTest">检索</el-button>
      </div>
      <div v-if="searchResult" class="muted" style="margin:10px 0">
        引擎：{{ searchResult.engine }} ｜ 向量块 {{ searchResult.vector_count }}/{{ searchResult.total_chunks }}
        <el-tag v-if="searchResult.degraded" type="warning" size="small">已降级为纯关键词</el-tag>
      </div>
      <div v-for="(h,i) in hits" :key="h.chunk_id" class="card" style="padding:12px;margin-bottom:8px">
        <b>{{ i + 1 }}. {{ h.doc_title }} #{{ h.idx + 1 }}</b>
        <span class="muted"> score {{ h.score }}</span>
        <div style="margin-top:6px">{{ h.content }}</div>
      </div>
    </div>

    <el-dialog v-model="dialog" :title="editing ? '编辑文档' : '新增文档'" width="620px">
      <el-form label-width="90px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="文件名"><el-input v-model="form.filename" placeholder="选填，如 选竿.md" /></el-form-item>
        <el-form-item label="正文"><el-input v-model="form.content" type="textarea" :rows="12" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存并切片</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="chunkDialog" title="切片预览" width="720px">
      <div v-for="c in chunks" :key="c.id" class="card" style="padding:10px;margin-bottom:8px">
        <div class="muted">#{{ c.idx }} ｜ {{ c.start }}-{{ c.end }} ｜
          <el-tag size="small" :type="c.has_vector ? 'success' : 'info'">{{ c.has_vector ? '有向量' : '无向量' }}</el-tag>
        </div>
        <div style="margin-top:6px">{{ c.content }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../../api'

const docs = ref<any[]>([])
const chunks = ref<any[]>([])
const hits = ref<any[]>([])
const searchResult = ref<any>(null)
const dialog = ref(false), chunkDialog = ref(false), editing = ref(false)
const form = ref<any>({ title: '', filename: '', content: '' })
const query = ref('新手选什么调性的竿'), topK = ref(3)

async function load() { const r: any = await api.docs(); docs.value = r.data || [] }
function open(row?: any) {
  editing.value = !!row
  form.value = row ? { id: row.id, title: row.title, filename: row.filename, content: '' } :
    { title: '', filename: '', content: '' }
  if (row) loadContent(row.id)
  dialog.value = true
}
async function loadContent(id: number) {
  const r: any = await api.doc(id)
  form.value.content = r.data.content
}
async function save() {
  const payload = { title: form.value.title, filename: form.value.filename, content: form.value.content }
  const r: any = editing.value ? await api.updateDoc(form.value.id, payload) : await api.createDoc(payload)
  ElMessage.success(`切片完成：${r.data.chunk_count} 块，引擎 ${r.data.engine}`)
  dialog.value = false
  load()
}
async function showChunks(row: any) {
  const r: any = await api.chunks(row.id)
  chunks.value = r.data || []
  chunkDialog.value = true
}
async function reindex(row: any) {
  const r: any = await api.reindex(row.id)
  ElMessage.success(`重建完成：${r.data.chunk_count} 块，向量 ${r.data.vector_count} 条`)
  load()
}
async function remove(row: any) { await api.deleteDoc(row.id); load() }
async function searchTest() {
  const r: any = await api.searchTest({ query: query.value, top_k: topK.value })
  searchResult.value = r.data
  hits.value = r.data.hits || []
}
onMounted(load)
</script>
