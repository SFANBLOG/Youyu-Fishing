<template>
  <div>
    <h2 class="section-title">全部商品</h2>
    <div class="card" style="padding:16px;display:flex;gap:12px;flex-wrap:wrap;align-items:center">
      <el-select v-model="category_id" placeholder="全部分类" clearable style="width:180px" @change="load(1)">
        <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-select v-model="sort" style="width:150px" @change="load(1)">
        <el-option label="默认排序" value="default" />
        <el-option label="价格从低到高" value="price_asc" />
        <el-option label="价格从高到低" value="price_desc" />
        <el-option label="销量优先" value="sales" />
        <el-option label="最新上架" value="new" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索商品名" style="width:220px" clearable @keyup.enter="load(1)" />
      <el-button type="primary" @click="load(1)">搜索</el-button>
    </div>

    <div class="grid-products" style="margin-top:18px">
      <ProductCard v-for="p in items" :key="p.id" :p="p" />
    </div>
    <el-empty v-if="!items.length" description="没有找到商品" />

    <div style="display:flex;justify-content:center;margin:24px 0">
      <el-pagination background layout="total, sizes, prev, pager, next, jumper"
                     :total="total" v-model:current-page="page" v-model:page-size="size"
                     :page-sizes="[8, 12, 20, 40]" @current-change="load(page)" @size-change="load(1)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api'
import ProductCard from '../../components/ProductCard.vue'

const route = useRoute()
const items = ref<any[]>([])
const categories = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(12)
const keyword = ref((route.query.keyword as string) || '')
const category_id = ref(route.query.category_id ? Number(route.query.category_id) : undefined)
const sort = ref('default')

async function load(p = 1) {
  page.value = p
  const res: any = await api.products({ page: p, size: size.value, keyword: keyword.value,
                                        category_id: category_id.value, sort: sort.value })
  items.value = res.data?.items || []
  total.value = res.data?.total || 0
}
onMounted(async () => {
  const c: any = await api.categories()
  categories.value = c.data || []
  load(1)
})
</script>
