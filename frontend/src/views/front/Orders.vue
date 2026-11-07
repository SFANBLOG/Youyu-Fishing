<template>
  <div>
    <h2 class="section-title">我的订单</h2>
    <el-tabs v-model="status" @tab-change="load">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="待支付" name="pending" />
      <el-tab-pane label="已支付" name="paid" />
      <el-tab-pane label="已发货" name="shipped" />
      <el-tab-pane label="已完成" name="completed" />
      <el-tab-pane label="已取消" name="cancelled" />
    </el-tabs>

    <div v-for="o in orders" :key="o.id" class="card" style="padding:16px;margin-bottom:14px">
      <div style="display:flex;justify-content:space-between">
        <span class="muted">订单号 {{ o.order_no }} ｜ {{ o.created_at }}</span>
        <el-tag :type="tagType(o.status)">{{ statusText(o.status) }}</el-tag>
      </div>
      <div v-for="i in o.items" :key="i.id" style="display:flex;gap:12px;align-items:center;margin:10px 0">
        <img :src="i.cover" style="width:60px;height:60px;object-fit:cover;border-radius:6px" />
        <span style="flex:1">{{ i.title }} × {{ i.quantity }}</span>
        <span class="price">¥{{ i.price }}</span>
      </div>
      <div style="display:flex;justify-content:flex-end;gap:8px;align-items:center">
        <span>合计 <span class="price">¥{{ o.total_amount }}</span></span>
        <el-button v-if="o.status === 'pending'" size="small" type="primary" @click="change(o, 'paid')">支付</el-button>
        <el-button v-if="o.status === 'pending' || o.status === 'paid'" size="small" @click="change(o, 'cancelled')">取消</el-button>
        <el-button v-if="o.status === 'shipped'" size="small" type="primary" @click="change(o, 'completed')">确认收货</el-button>
        <el-button v-if="o.status === 'completed'" size="small" @click="review(o)">评价</el-button>
      </div>
    </div>
    <el-empty v-if="!orders.length" description="暂无订单" />

    <el-dialog v-model="showReview" title="发表评价" width="440px">
      <el-rate v-model="rating" />
      <el-input v-model="content" type="textarea" :rows="4" placeholder="说说使用感受" style="margin-top:12px" />
      <template #footer>
        <el-button @click="showReview = false">取消</el-button>
        <el-button type="primary" @click="submitReview">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../../api'

const orders = ref<any[]>([])
const status = ref('')
const showReview = ref(false)
const rating = ref(5)
const content = ref('')
const current = ref<any>(null)

const statusText = (s: string) => ({ pending: '待支付', paid: '已支付', shipped: '已发货',
                                     completed: '已完成', cancelled: '已取消' } as any)[s] || s
const tagType = (s: string) => ({ pending: 'warning', paid: 'primary', shipped: 'info',
                                  completed: 'success', cancelled: 'danger' } as any)[s] || 'info'

async function load() {
  const res: any = await api.orders({ status: status.value, size: 50 })
  orders.value = res.data?.items || []
}
async function change(o: any, s: string) {
  await api.orderStatus(o.id, s)
  ElMessage.success('状态已更新')
  load()
}
function review(o: any) { current.value = o; showReview.value = true }
async function submitReview() {
  const item = current.value?.items?.[0]
  if (!item) return
  await api.createReview({ product_id: item.product_id, order_id: current.value.id,
                           rating: rating.value, content: content.value })
  ElMessage.success('评价成功')
  showReview.value = false
  content.value = ''
}
onMounted(load)
</script>
