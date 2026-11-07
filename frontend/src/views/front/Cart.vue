<template>
  <div>
    <h2 class="section-title">购物车</h2>
    <div class="card" style="padding:16px">
      <div style="display:flex;justify-content:space-between;margin-bottom:12px">
        <el-checkbox :model-value="allChecked" @change="toggleAll">全选</el-checkbox>
        <div>
          <el-button size="small" @click="batchDelete" :disabled="!checkedIds.length">批量删除</el-button>
          <el-button size="small" type="danger" plain @click="clear">清空</el-button>
        </div>
      </div>
      <div v-for="i in items" :key="i.id" style="display:flex;align-items:center;gap:14px;padding:12px 0;border-top:1px solid #f3f4f6">
        <el-checkbox :model-value="i.checked" @change="(v:any) => toggle(i.id, v)" />
        <img :src="i.cover" style="width:80px;height:80px;object-fit:cover;border-radius:8px" />
        <div style="flex:1">
          <div>{{ i.title }}</div>
          <div class="muted">{{ i.spec }}</div>
        </div>
        <span class="price">¥{{ i.price }}</span>
        <el-input-number :model-value="i.quantity" :min="1" size="small"
                         @change="(v:any) => changeQty(i.id, v)" />
        <el-button text type="danger" @click="remove(i.id)">删除</el-button>
      </div>
      <el-empty v-if="!items.length" description="购物车还是空的" />
      <div style="display:flex;justify-content:flex-end;align-items:center;gap:16px;margin-top:18px">
        <span>合计：<span class="price" style="font-size:22px">¥{{ totalAmount }}</span></span>
        <el-button type="primary" size="large" :disabled="!checkedIds.length"
                   @click="$router.push({path:'/checkout', query:{ids: checkedIds.join(',')}})">去结算</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api'
import { bus, CART_CHANGED } from '../../utils/eventBus'

const items = ref<any[]>([])
const totalAmount = ref(0)
const checkedIds = computed(() => items.value.filter((i) => i.checked).map((i) => i.id))
const allChecked = computed(() => !!items.value.length && items.value.every((i) => i.checked))

async function load() {
  const res: any = await api.cart()
  items.value = res.data?.items || []
  totalAmount.value = res.data?.total_amount || 0
}
async function toggle(id: number, checked: boolean) { await api.updateCart(id, { checked }); load() }
async function changeQty(id: number, quantity: number) { await api.updateCart(id, { quantity }); load() }
async function toggleAll(v: any) { await api.checkAll(!!v); load() }
async function batchDelete() { await api.batchDeleteCart(checkedIds.value); bus.emit(CART_CHANGED); load() }
async function clear() { await api.clearCart(); bus.emit(CART_CHANGED); load() }
async function remove(id: number) { await api.batchDeleteCart([id]); bus.emit(CART_CHANGED); load() }
onMounted(load)
</script>
