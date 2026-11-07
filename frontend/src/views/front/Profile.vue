<template>
  <div style="max-width:680px;margin:30px auto" class="card">
    <div style="padding:24px">
      <h2>个人中心</h2>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="账号">{{ user?.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ user?.nickname }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ user?.role === 'admin' ? '管理员' : '会员' }}</el-descriptions-item>
      </el-descriptions>
      <div style="display:flex;gap:10px;margin-top:20px;flex-wrap:wrap">
        <el-button @click="$router.push('/orders')">我的订单</el-button>
        <el-button @click="$router.push('/favorites')">我的收藏</el-button>
        <el-button @click="$router.push('/ai')">AI 选竿助手</el-button>
        <el-button v-if="user?.role === 'admin'" type="primary" @click="$router.push('/admin')">后台管理</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const raw = localStorage.getItem('yy_user')
const user = ref(raw ? JSON.parse(raw) : null)
</script>
