<template>
  <div class="admin-layout">
    <aside class="admin-side">
      <div style="padding:20px 16px;font-size:18px;font-weight:800;color:#fff">有渔 · 管理后台</div>
      <el-menu :default-active="$route.path" router background-color="#0b3d2e"
               text-color="#a7f3d0" active-text-color="#fff" style="border-right:0">
        <el-menu-item index="/admin"><el-icon><DataBoard /></el-icon>数据看板</el-menu-item>
        <el-sub-menu index="shop">
          <template #title><el-icon><Goods /></el-icon>商城管理</template>
          <el-menu-item index="/admin/categories">分类管理</el-menu-item>
          <el-menu-item index="/admin/products">商品管理</el-menu-item>
          <el-menu-item index="/admin/orders">订单管理</el-menu-item>
          <el-menu-item index="/admin/reviews">评价管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="cms">
          <template #title><el-icon><Document /></el-icon>内容管理</template>
          <el-menu-item index="/admin/news">资讯管理</el-menu-item>
          <el-menu-item index="/admin/banners">轮播图</el-menu-item>
          <el-menu-item index="/admin/notices">公告管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="users">
          <template #title><el-icon><User /></el-icon>账号管理</template>
          <el-menu-item index="/admin/admins">管理员</el-menu-item>
          <el-menu-item index="/admin/members">会员管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="ai">
          <template #title><el-icon><MagicStick /></el-icon>AI 能力中心</template>
          <el-menu-item index="/admin/models">模型配置</el-menu-item>
          <el-menu-item index="/admin/prompts">提示词配置</el-menu-item>
          <el-menu-item index="/admin/knowledge">知识库管理</el-menu-item>
          <el-menu-item index="/admin/chat-records">对话记录</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </aside>

    <main class="admin-main">
      <div class="admin-top" style="display:flex;justify-content:space-between;align-items:center">
        <span class="muted">后台 / {{ $route.meta.crud?.title || $route.name }}</span>
        <div>
          <el-button text @click="$router.push('/')">返回前台</el-button>
          <el-button text type="danger" @click="logout">退出登录</el-button>
        </div>
      </div>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { DataBoard, Goods, Document, User, MagicStick } from '@element-plus/icons-vue'
const router = useRouter()
function logout() {
  localStorage.removeItem('yy_token')
  localStorage.removeItem('yy_role')
  localStorage.removeItem('yy_user')
  router.push('/admin/login')
}
</script>
