<template>
  <div class="card" style="padding:18px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div>
        <h2 style="margin:0">对话记录（全链路可观测）</h2>
        <div class="muted">前台只看到回答，这里保留意图、工具、引擎、执行轨迹、引用与推荐</div>
      </div>
      <el-input v-model="keyword" placeholder="搜内容" style="width:220px" @keyup.enter="load(1)" />
    </div>

    <el-table :data="rows" border @row-click="openDetail" style="cursor:pointer">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="session_id" label="会话" width="80" />
      <el-table-column prop="role" label="角色" width="90" />
      <el-table-column prop="content" label="内容" show-overflow-tooltip />
      <el-table-column prop="intent" label="意图" width="100" />
      <el-table-column prop="tool" label="工具" width="150" />
      <el-table-column prop="engine" label="引擎" width="180" />
      <el-table-column label="降级" width="80">
        <template #default="{row}"><el-tag v-if="row.degraded" type="warning" size="small">兜底</el-tag></template>
      </el-table-column>
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:14px">
      <el-pagination background layout="total, sizes, prev, pager, next, jumper"
                     :total="total" v-model:current-page="page" v-model:page-size="size"
                     :page-sizes="[10,20,50]" @current-change="load(page)" @size-change="load(1)" />
    </div>

    <el-drawer v-model="drawer" title="消息详情" size="560px">
      <template v-if="detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="角色">{{ detail.role }}</el-descriptions-item>
          <el-descriptions-item label="意图">{{ detail.intent }}</el-descriptions-item>
          <el-descriptions-item label="工具">{{ detail.tool }}</el-descriptions-item>
          <el-descriptions-item label="引擎">{{ detail.engine }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin-top:18px">正文</h4>
        <div class="card" style="padding:12px;white-space:pre-wrap">{{ detail.content }}</div>

        <h4>Agent 执行轨迹</h4>
        <el-timeline>
          <el-timeline-item v-for="(t,i) in detail.trace" :key="i" :timestamp="String(t.ts)">
            <b>{{ t.node }}</b>：{{ t.detail }}
          </el-timeline-item>
        </el-timeline>
        <el-empty v-if="!detail.trace?.length" description="无轨迹" :image-size="50" />

        <h4 v-if="detail.sources?.length">引用来源</h4>
        <div v-for="s in detail.sources" :key="s.chunk_id" class="muted" style="margin-bottom:6px">
          {{ s.doc_title }} #{{ s.idx + 1 }}：{{ s.content?.slice(0, 80) }}...
        </div>

        <h4 v-if="detail.recommendations?.length">推荐商品</h4>
        <el-tag v-for="p in detail.recommendations" :key="p.id" style="margin:2px">{{ p.title }}</el-tag>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../../api'

const rows = ref<any[]>([])
const total = ref(0), page = ref(1), size = ref(20)
const keyword = ref('')
const drawer = ref(false)
const detail = ref<any>(null)

async function load(p = 1) {
  page.value = p
  const r: any = await api.chatRecords({ page: p, size: size.value, keyword: keyword.value })
  rows.value = r.data?.items || []
  total.value = r.data?.total || 0
}
function openDetail(row: any) { detail.value = row; drawer.value = true }
onMounted(() => load(1))
</script>
