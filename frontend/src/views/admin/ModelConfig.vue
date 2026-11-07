<template>
  <div class="card" style="padding:18px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div>
        <h2 style="margin:0">模型配置</h2>
        <div class="muted">支持 OpenAI / DeepSeek / 通义 / 智谱 / 硅基流动 / Ollama 等任意 OpenAI 兼容协议</div>
      </div>
      <el-button type="primary" @click="open()">新增模型</el-button>
    </div>

    <el-table :data="rows" border>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="provider" label="服务商" width="140" />
      <el-table-column prop="model_name" label="模型 ID" />
      <el-table-column prop="model_type" label="类型" width="110">
        <template #default="{row}">{{ typeText(row.model_type) }}</template>
      </el-table-column>
      <el-table-column prop="api_key" label="API Key" width="160" />
      <el-table-column label="默认" width="90">
        <template #default="{row}"><el-tag v-if="row.is_default" type="success">默认</el-tag></template>
      </el-table-column>
      <el-table-column label="多模态" width="90">
        <template #default="{row}"><el-tag v-if="row.is_multimodal" type="warning">Vision</el-tag></template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{row}"><el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '启用' : '停用' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{row}">
          <el-button size="small" @click="test(row)">测试连接</el-button>
          <el-button size="small" @click="setDefault(row)" :disabled="row.is_default">设为默认</el-button>
          <el-button size="small" @click="open(row)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editing ? '编辑模型' : '新增模型'" width="580px">
      <el-form label-width="110px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="服务商"><el-input v-model="form.provider" placeholder="openai-compatible" /></el-form-item>
        <el-form-item label="Base URL"><el-input v-model="form.base_url" placeholder="https://api.deepseek.com/v1" /></el-form-item>
        <el-form-item label="API Key"><el-input v-model="form.api_key" type="password" show-password /></el-form-item>
        <el-form-item label="模型 ID"><el-input v-model="form.model_name" placeholder="deepseek-chat" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.model_type" style="width:100%">
            <el-option label="对话模型" value="chat" />
            <el-option label="向量模型" value="embedding" />
            <el-option label="视觉模型" value="vision" />
          </el-select>
        </el-form-item>
        <el-form-item label="默认"><el-switch v-model="form.is_default" /></el-form-item>
        <el-form-item label="多模态"><el-switch v-model="form.is_multimodal" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.enabled" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../../api'

const rows = ref<any[]>([])
const dialog = ref(false), editing = ref(false)
const form = ref<any>({})
const typeText = (t: string) => ({ chat: '对话', embedding: '向量', vision: '视觉' } as any)[t] || t

async function load() { const r: any = await api.models(); rows.value = r.data || [] }
function open(row?: any) {
  editing.value = !!row
  form.value = row ? { ...row, api_key: '' } : { name: '', provider: 'openai-compatible', base_url: '',
    api_key: '', model_name: '', model_type: 'chat', is_default: false,
    is_multimodal: false, enabled: true }
  dialog.value = true
}
async function save() {
  const payload = { ...form.value }
  if (!payload.api_key) delete payload.api_key
  if (editing.value) await api.updateModel(payload.id, payload)
  else await api.createModel(payload)
  ElMessage.success('保存成功')
  dialog.value = false
  load()
}
async function test(row: any) {
  const r: any = await api.testModel(row.id)
  const d = r.data
  ElMessage({ type: d.ok ? 'success' : 'error', message: d.message, duration: 4000 })
}
async function setDefault(row: any) { await api.setDefaultModel(row.id); load() }
async function remove(row: any) { await api.deleteModel(row.id); load() }
onMounted(load)
</script>
