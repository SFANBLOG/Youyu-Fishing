<template>
  <div>
    <header class="yy-header">
      <div class="container inner">
        <router-link to="/" class="yy-logo">有渔 · YOUYU</router-link>
        <nav class="yy-nav">
          <router-link to="/">首页</router-link>
          <router-link to="/products">全部商品</router-link>
          <router-link to="/news">钓鱼资讯</router-link>
          <router-link to="/ai">AI 选竿助手</router-link>
        </nav>
        <el-input v-model="kw" placeholder="搜商品" style="width:180px" @keyup.enter="search">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-badge :value="cartState.count" :hidden="!cartState.count">
          <el-button circle @click="$router.push('/cart')"><el-icon><ShoppingCart /></el-icon></el-button>
        </el-badge>
        <el-button text @click="openNotices">公告</el-button>
        <el-dropdown v-if="user" @command="onCommand">
          <span style="cursor:pointer">{{ user.nickname || user.username }} ▾</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="orders">我的订单</el-dropdown-item>
              <el-dropdown-item command="favorites">我的收藏</el-dropdown-item>
              <el-dropdown-item v-if="user.role === 'admin'" command="admin">后台管理</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button v-else type="primary" size="small" @click="$router.push('/login')">登录</el-button>
      </div>
    </header>

    <main class="container" style="min-height:70vh;padding-bottom:40px">
      <router-view />
    </main>

    <footer style="background:#0b3d2e;color:#a7f3d0;padding:24px;text-align:center;font-size:13px">
      有渔渔具 AI Agent · FastAPI + LangGraph + Vue3 示例项目
    </footer>

    <el-drawer v-model="drawer" title="最新公告" direction="rtl" size="360px">
      <div v-for="n in notices" :key="n.id" style="margin-bottom:18px">
        <h4>{{ n.title }}</h4>
        <p class="muted" style="white-space:pre-wrap">{{ n.content }}</p>
      </div>
      <el-empty v-if="!notices.length" description="暂无公告" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, ShoppingCart } from '@element-plus/icons-vue'
import { api } from '../../api'
import { bus, CART_CHANGED } from '../../utils/eventBus'
import { cartState, refreshCart } from '../../stores/cart'

const router = useRouter()
const kw = ref('')
const drawer = ref(false)
const notices = ref<any[]>([])
const user = ref<any>(null)

const search = () => router.push({ path: '/products', query: { keyword: kw.value } })

async function openNotices() {
  drawer.value = true
  const res: any = await api.notices()
  notices.value = res.data || []
}

function loadUser() {
  const raw = localStorage.getItem('yy_user')
  user.value = raw ? JSON.parse(raw) : null
}

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    localStorage.removeItem('yy_token')
    localStorage.removeItem('yy_role')
    localStorage.removeItem('yy_user')
    loadUser()
    refreshCart()
    router.push('/')
    return
  }
  router.push(cmd === 'admin' ? '/admin' : `/${cmd}`)
}

bus.on(CART_CHANGED, loadUser)
onMounted(() => {
  loadUser()
  refreshCart()
})
</script>
