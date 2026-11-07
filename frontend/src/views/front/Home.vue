<template>
  <div>
    <el-carousel class="hero" height="320px" v-if="banners.length">
      <el-carousel-item v-for="b in banners" :key="b.id" @click="$router.push(b.link || '/products')">
        <img :src="b.image" :alt="b.title" style="width:100%;height:100%;object-fit:cover;cursor:pointer" />
      </el-carousel-item>
    </el-carousel>

    <div class="card" style="margin-top:16px;padding:12px 16px;display:flex;gap:12px;align-items:center">
      <el-tag type="warning">公告</el-tag>
      <span v-if="notices.length" class="muted" @click="showNotice = true" style="cursor:pointer;flex:1">
        {{ notices[0].title }}
      </span>
      <span v-else class="muted">暂无公告</span>
    </div>

    <h2 class="section-title">分类导航</h2>
    <div style="display:flex;gap:10px;flex-wrap:wrap">
      <el-button v-for="c in categories" :key="c.id" round
                 @click="$router.push({path:'/products', query:{category_id:c.id}})">{{ c.name }}</el-button>
    </div>

    <h2 class="section-title">为你推荐</h2>
    <div class="grid-products">
      <ProductCard v-for="p in recommend" :key="p.id" :p="p" />
    </div>

    <h2 class="section-title">热销榜</h2>
    <div class="grid-products">
      <ProductCard v-for="p in hot" :key="p.id" :p="p" />
    </div>

    <h2 class="section-title">最新资讯</h2>
    <div class="card" style="padding:8px 20px">
      <div v-for="n in news" :key="n.id" style="padding:12px 0;border-bottom:1px solid #f3f4f6;cursor:pointer"
           @click="$router.push(`/news/${n.id}`)">
        <b>{{ n.title }}</b>
        <div class="muted">{{ n.summary }}</div>
      </div>
    </div>

    <el-dialog v-model="showNotice" :title="notices[0]?.title" width="480px">
      <div style="white-space:pre-wrap">{{ notices[0]?.content }}</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../../api'
import ProductCard from '../../components/ProductCard.vue'

const banners = ref<any[]>([])
const notices = ref<any[]>([])
const categories = ref<any[]>([])
const recommend = ref<any[]>([])
const hot = ref<any[]>([])
const news = ref<any[]>([])
const showNotice = ref(false)

onMounted(async () => {
  const [b, n, c, r, h, nw]: any[] = await Promise.all([
    api.banners(), api.notices(), api.categories(),
    api.products({ size: 8, sort: 'new' }),
    api.products({ size: 4, sort: 'sales' }),
    api.news({ size: 3 }),
  ])
  banners.value = b.data || []
  notices.value = n.data || []
  categories.value = c.data || []
  recommend.value = r.data?.items || []
  hot.value = h.data?.items || []
  news.value = nw.data?.items || []
})
</script>
