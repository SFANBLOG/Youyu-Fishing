<template>
  <div>
    <h2 class="section-title">确认订单</h2>
    <div class="card" style="padding:20px">
      <h3>收货信息</h3>
      <el-form label-width="90px" style="max-width:560px">
        <el-form-item label="收货人"><el-input v-model="address.name" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="address.phone" /></el-form-item>
        <el-form-item label="详细地址"><el-input v-model="address.detail" type="textarea" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="remark" /></el-form-item>
      </el-form>

      <h3>商品清单</h3>
      <div v-for="i in items" :key="i.id" style="display:flex;gap:12px;align-items:center;padding:8px 0">
        <img :src="i.cover" style="width:56px;height:56px;object-fit:cover;border-radius:6px" />
        <span style="flex:1">{{ i.title }} × {{ i.quantity }}</span>
        <span class="price">¥{{ (i.price * i.quantity).toFixed(2) }}</span>
      </div>

      <div style="display:flex;justify-content:flex-end;align-items:center;gap:18px;margin-top:20px">
        <span>应付：<span class="price" style="font-size:24px">¥{{ total }}</span></span>
        <el-button type="primary" size="large" :disabled="!items.length" @click="submit">提交订单</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../../api'
import { bus, CART_CHANGED } from '../../utils/eventBus'

const route = useRoute()
const router = useRouter()
const ids = String(route.query.ids || '').split(',').filter(Boolean).map(Number)
const all = ref<any[]>([])
const address = ref({ name: '', phone: '', detail: '' })
const remark = ref('')
const items = computed(() => all.value.filter((i) => ids.includes(i.id)))
const total = computed(() => items.value.reduce((s, i) => s + i.price * i.quantity, 0).toFixed(2))

async function submit() {
  if (!address.value.name || !address.value.phone) {
    ElMessage.warning('请填写收货人和手机号')
    return
  }
  await api.createOrder({ cart_ids: ids, address: address.value, remark: remark.value })
  ElMessage.success('下单成功')
  bus.emit(CART_CHANGED)
  router.push('/orders')
}
onMounted(async () => {
  const res: any = await api.cart()
  all.value = res.data?.items || []
})
</script>
