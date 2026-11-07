<template>
  <div v-if="p">
    <el-breadcrumb separator="/" style="margin:18px 0">
      <el-breadcrumb-item :to="{path:'/'}">首页</el-breadcrumb-item>
      <el-breadcrumb-item :to="{path:'/products'}">全部商品</el-breadcrumb-item>
      <el-breadcrumb-item>{{ p.title }}</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="card" style="padding:20px;display:grid;grid-template-columns:420px 1fr;gap:28px">
      <div>
        <img :src="activeImage" style="width:100%;height:340px;object-fit:cover;border-radius:10px" />
        <div style="display:flex;gap:8px;margin-top:10px">
          <img v-for="(img,i) in p.images" :key="i" :src="img" @click="activeImage = img"
               style="width:64px;height:64px;object-fit:cover;border-radius:6px;cursor:pointer;border:2px solid #eee" />
        </div>
      </div>
      <div>
        <h1 style="font-size:24px;margin:0 0 8px">{{ p.title }}</h1>
        <div class="muted">{{ p.subtitle }}</div>
        <div style="margin:18px 0">
          <span class="price" style="font-size:30px">¥{{ p.price }}</span>
          <span class="muted" style="text-decoration:line-through;margin-left:10px">¥{{ p.original_price }}</span>
        </div>
        <div class="muted">销量 {{ p.sales }} ｜ 库存 {{ p.stock }}</div>
        <div style="margin:18px 0" v-for="(s,i) in p.specs" :key="i">
          <span style="margin-right:12px">{{ s.name }}</span>
          <el-radio-group v-model="spec[i]">
            <el-radio-button v-for="o in s.options" :key="o" :value="o">{{ o }}</el-radio-button>
          </el-radio-group>
        </div>
        <div style="display:flex;gap:10px;margin-top:20px">
          <el-button type="primary" size="large" @click="addCart">加入购物车</el-button>
          <el-button size="large" @click="toggleFav">{{ faved ? '取消收藏' : '收藏' }}</el-button>
        </div>
      </div>
    </div>

    <h2 class="section-title">商品详情</h2>
    <div class="card" style="padding:20px" v-html="p.detail"></div>

    <h2 class="section-title">用户评价</h2>
    <div class="card" style="padding:16px">
      <div v-for="r in reviews" :key="r.id" style="padding:8px 0;border-bottom:1px solid #f3f4f6">
        <b>{{ r.user }}</b> <el-rate :model-value="r.rating" disabled size="small" />
        <div>{{ r.content }}</div>
      </div>
      <el-empty v-if="!reviews.length" description="暂无评价" :image-size="60" />
    </div>

    <h2 class="section-title">相似推荐</h2>
    <div class="grid-products">
      <ProductCard v-for="s in similar" :key="s.id" :p="s" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../../api'
import { bus, CART_CHANGED } from '../../utils/eventBus'
import ProductCard from '../../components/ProductCard.vue'

const route = useRoute()
const id = Number(route.params.id)
const p = ref<any>(null)
const activeImage = ref('')
const spec = ref<string[]>([])
const reviews = ref<any[]>([])
const similar = ref<any[]>([])
const faved = ref(false)

async function addCart() {
  await api.addCart({ product_id: id, quantity: 1, spec: spec.value.join('/') })
  ElMessage.success('已加入购物车')
  bus.emit(CART_CHANGED)
}
async function toggleFav() {
  if (faved.value) await api.removeFavorite(id)
  else await api.addFavorite(id)
  faved.value = !faved.value
  ElMessage.success(faved.value ? '已收藏' : '已取消收藏')
}
onMounted(async () => {
  const [d, r, s, f]: any[] = await Promise.all([
    api.product(id), api.reviews({ product_id: id }), api.similar(id), api.favorites().catch(() => ({ data: [] })),
  ])
  p.value = d.data
  activeImage.value = d.data.cover
  reviews.value = r.data?.items || []
  similar.value = s.data || []
  faved.value = (f.data || []).some((x: any) => x.id === id)
})
</script>
