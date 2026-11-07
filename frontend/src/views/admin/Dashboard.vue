<template>
  <div>
    <el-row :gutter="14">
      <el-col :span="4" v-for="(v,k) in cards" :key="k">
        <div class="card" style="padding:16px;text-align:center">
          <div class="muted">{{ label(k) }}</div>
          <div style="font-size:24px;font-weight:700;color:#0f766e;margin-top:6px">{{ v }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="14" style="margin-top:16px">
      <el-col :span="8">
        <div class="card" style="padding:16px">
          <h3>订单状态分布</h3>
          <EChart :option="pieOption" />
        </div>
      </el-col>
      <el-col :span="8">
        <div class="card" style="padding:16px">
          <h3>分类商品数</h3>
          <EChart :option="catOption" />
        </div>
      </el-col>
      <el-col :span="8">
        <div class="card" style="padding:16px">
          <h3>热销 Top10</h3>
          <EChart :option="hotOption" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api'
import EChart from '../../components/EChart.vue'

const data = ref<any>({ cards: {}, order_status: [], category_bar: { categories: [], values: [] },
                        hot_bar: { names: [], values: [] } })
const cards = computed(() => data.value.cards || {})
const label = (k: string) => ({ products: '商品数', orders: '订单数', members: '会员数',
  reviews: '评价数', knowledge_docs: '知识文档', chat_messages: '对话消息', revenue: '成交额(元)' } as any)[k] || k

const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { fontSize: 11 } },
  series: [{ type: 'pie', radius: ['42%', '68%'], data: data.value.order_status }],
}))
const catOption = computed(() => ({
  tooltip: {}, grid: { left: 80, right: 16 },
  xAxis: { type: 'value' }, yAxis: { type: 'category', data: data.value.category_bar?.categories || [] },
  series: [{ type: 'bar', data: data.value.category_bar?.values || [], itemStyle: { color: '#0f766e' } }],
}))
const hotOption = computed(() => ({
  tooltip: {}, grid: { left: 16, right: 16, bottom: 70 },
  xAxis: { type: 'category', data: data.value.hot_bar?.names || [], axisLabel: { rotate: 45, fontSize: 9 } },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: data.value.hot_bar?.values || [], itemStyle: { color: '#f59e0b' } }],
}))

onMounted(async () => {
  const r: any = await api.dashboard()
  data.value = r.data
})
</script>
